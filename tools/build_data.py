"""Turn Overpass JSON (roads + addresses) into a compact routing graph for the map page.

Usage: python3 -I build_data.py roads.json addresses.json out.json
"""
import json, math, sys
from collections import defaultdict

roads_path, addr_path, out_path = sys.argv[1:4]

CLASSES = ["motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link",
           "secondary", "secondary_link", "tertiary", "tertiary_link", "unclassified",
           "residential", "living_street", "service", "road", "busway"]
CLS = {c: i for i, c in enumerate(CLASSES)}
NO_SNAP = {"motorway", "motorway_link", "trunk_link", "busway"}
SKIP_SERVICE = {"parking_aisle", "driveway", "drive-through", "emergency_access"}
YES = {"yes", "designated", "permissive", "destination"}


def parse_maxspeed(v):
    if not v:
        return 0
    v = v.strip().lower()
    named = {"nl:urban": 50, "nl:rural": 80, "nl:zone30": 30, "nl:zone60": 60,
             "nl:motorway": 100, "nl:trunk": 100, "walk": 15, "nl:living_street": 15}
    if v in named:
        return named[v]
    num = ""
    for ch in v:
        if ch.isdigit():
            num += ch
        elif num:
            break
    return int(num) if num else 0


def way_attrs(t):
    hw = t.get("highway")
    if hw not in CLS:
        return None
    if t.get("area") == "yes":
        return None
    if hw == "service" and t.get("service") in SKIP_SERVICE:
        return None
    access = t.get("access", "")
    mv = t.get("motor_vehicle", t.get("motorcar", t.get("vehicle", "")))
    emergency = t.get("emergency", "")
    bus_only = 0
    if hw == "busway" or t.get("bus") == "designated" and access in ("no", "private") or \
            (access in ("no", "private") and mv not in YES and
             (t.get("psv") in YES or t.get("bus") in YES or emergency in YES)):
        bus_only = 1
    elif access in ("no", "private") and mv not in YES:
        return None
    elif mv in ("no", "private") and emergency not in YES and t.get("psv") not in YES:
        return None
    if emergency == "no":
        return None
    ow = t.get("oneway", "")
    if ow in ("yes", "true", "1"):
        oneway = 1
    elif ow == "-1":
        oneway = -1
    elif ow == "no":
        oneway = 0
    elif t.get("junction") in ("roundabout", "circular") or hw in ("motorway", "motorway_link"):
        oneway = 1
    else:
        oneway = 0
    name = t.get("name") or t.get("ref") or ""
    ref = t.get("ref", "")
    return (CLS[hw], parse_maxspeed(t.get("maxspeed")), oneway, bus_only, name, ref)


roads = json.load(open(roads_path))["elements"]
nodes = {}
ways = []
boundary = []
for el in roads:
    if el["type"] == "node":
        nodes[el["id"]] = (el["lat"], el["lon"])
    elif el["type"] == "way":
        a = way_attrs(el.get("tags", {}))
        if a:
            ways.append((el["nodes"], a))
    elif el["type"] == "relation":
        for m in el.get("members", []):
            if m.get("role") == "outer" and m.get("geometry"):
                boundary.append([(g["lat"], g["lon"]) for g in m["geometry"]])

# Graph vertices: way ends and nodes shared by more than one way occurrence.
use = defaultdict(int)
for nds, _ in ways:
    for n in nds:
        use[n] += 1
    use[nds[0]] += 1
    use[nds[-1]] += 1

lat0 = 52.17
KX = 111320 * math.cos(math.radians(lat0))
KY = 110540


def dist(p, q):
    return math.hypot((p[1] - q[1]) * KX, (p[0] - q[0]) * KY)


attr_table, attr_idx = [], {}
name_table, name_idx = [""], {"": 0}
vid = {}
edges = []  # (u, v, attr, length, [points])
for nds, a in ways:
    nds = [n for n in nds if n in nodes]
    if len(nds) < 2:
        continue
    key = a[:4] + (a[4],)
    if a[4] not in name_idx:
        name_idx[a[4]] = len(name_table)
        name_table.append(a[4])
    k = (a[0], a[1], a[2], a[3], name_idx[a[4]])
    if k not in attr_idx:
        attr_idx[k] = len(attr_table)
        attr_table.append(list(k))
    ai = attr_idx[k]
    start = 0
    for i in range(1, len(nds)):
        if use[nds[i]] > 1 or i == len(nds) - 1:
            chain = nds[start:i + 1]
            if chain[0] != chain[-1] or len(chain) > 2:
                pts = [nodes[n] for n in chain]
                length = sum(dist(pts[j], pts[j + 1]) for j in range(len(pts) - 1))
                for n in (chain[0], chain[-1]):
                    if n not in vid:
                        vid[n] = len(vid)
                edges.append((vid[chain[0]], vid[chain[-1]], ai, length, pts, a[0]))
            start = i

# A1 latitude as a function of longitude, for the north/south split.
a1 = []
for nds, a in ways:
    if a[0] == CLS["motorway"] and "A1" in a[5].replace(" ", "").split(";"):
        a1 += [nodes[n] for n in nds if n in nodes]
a1.sort(key=lambda p: p[1])
bins = defaultdict(list)
for la, lo in a1:
    bins[round(lo, 3)].append(la)
a1_line = sorted((lo, sum(v) / len(v)) for lo, v in bins.items())


def a1_lat(lon):
    if not a1_line:
        return 52.165
    if lon <= a1_line[0][0]:
        return a1_line[0][1]
    if lon >= a1_line[-1][0]:
        return a1_line[-1][1]
    lo, hi = 0, len(a1_line) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if a1_line[mid][0] <= lon:
            lo = mid
        else:
            hi = mid
    (x0, y0), (x1, y1) = a1_line[lo], a1_line[hi]
    return y0 + (y1 - y0) * (lon - x0) / (x1 - x0 or 1)


# Snap addresses to the nearest point on a snappable edge segment.
CELL = 0.002
grid = defaultdict(list)
for ei, e in enumerate(edges):
    if CLASSES[e[5]] in NO_SNAP:
        continue
    pts = e[4]
    for j in range(len(pts) - 1):
        p, q = pts[j], pts[j + 1]
        for gx in range(int(min(p[1], q[1]) / CELL), int(max(p[1], q[1]) / CELL) + 1):
            for gy in range(int(min(p[0], q[0]) / CELL), int(max(p[0], q[0]) / CELL) + 1):
                grid[(gx, gy)].append((ei, j))

addrs_raw = json.load(open(addr_path))["elements"]
seen = set()
addrs = []
for el in addrs_raw:
    if "lat" in el:
        la, lo = el["lat"], el["lon"]
    elif "center" in el:
        la, lo = el["center"]["lat"], el["center"]["lon"]
    else:
        continue
    t = el.get("tags", {})
    key = (t.get("addr:postcode"), t.get("addr:housenumber"), t.get("addr:housenumber:addition", ""),
           t.get("addr:street"), round(la, 5), round(lo, 5))
    if key in seen:
        continue
    seen.add(key)
    addrs.append((la, lo))

seg_len = {}
addr_out = []
for la, lo in addrs:
    gx, gy = int(lo / CELL), int(la / CELL)
    best = None
    for r in (1, 2, 4):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                for ei, j in grid.get((gx + dx, gy + dy), ()):
                    pts = edges[ei][4]
                    p, q = pts[j], pts[j + 1]
                    px, py = (p[1] - lo) * KX, (p[0] - la) * KY
                    qx, qy = (q[1] - lo) * KX, (q[0] - la) * KY
                    dx_, dy_ = qx - px, qy - py
                    L2 = dx_ * dx_ + dy_ * dy_
                    s = 0 if L2 == 0 else max(0, min(1, -(px * dx_ + py * dy_) / L2))
                    d = math.hypot(px + s * dx_, py + s * dy_)
                    if best is None or d < best[0]:
                        best = (d, ei, j, s)
        if best:
            break
    if not best or best[0] > 300:
        continue
    d, ei, j, s = best
    pts = edges[ei][4]
    along = sum(dist(pts[k], pts[k + 1]) for k in range(j)) + s * dist(pts[j], pts[j + 1])
    frac = along / edges[ei][3] if edges[ei][3] else 0
    addr_out.append((la, lo, ei, frac, 1 if la > a1_lat(lo) else 0))

# Encode: coordinates as integer 1e-5 degrees, delta-coded within each edge.
def enc(p):
    return (round(p[0] * 1e5), round(p[1] * 1e5))

E_u, E_v, E_a, E_len, E_np, coords = [], [], [], [], [], []
for u, v, ai, length, pts, _ in edges:
    E_u.append(u); E_v.append(v); E_a.append(ai); E_len.append(round(length, 1)); E_np.append(len(pts))
    prev = (0, 0)
    for p in pts:
        c = enc(p)
        coords += [c[0] - prev[0], c[1] - prev[1]]
        prev = c

out = {
    "classes": CLASSES,
    "attrs": attr_table,
    "names": name_table,
    "nv": len(vid),
    "eu": E_u, "ev": E_v, "ea": E_a, "elen": E_len, "enp": E_np, "coords": coords,
    "addr": [[round(a[0] * 1e5), round(a[1] * 1e5), a[2], round(a[3], 3), a[4]] for a in addr_out],
    "boundary": [[enc(p) for p in ring] for ring in boundary],
    "a1": [[round(lo * 1e5), round(la * 1e5)] for lo, la in a1_line],
}
json.dump(out, open(out_path, "w"), separators=(",", ":"))
print(f"vertices {len(vid)}, edges {len(edges)}, addresses {len(addr_out)}/{len(addrs)}, "
      f"boundary rings {len(boundary)}, A1 pts {len(a1_line)}")
