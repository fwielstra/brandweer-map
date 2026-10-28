"""Add stitched municipal boundary rings and station places to graph.json.
Usage: python3 -I augment.py roads.json graph.json"""
import json, sys
roads_path, graph_path = sys.argv[1:3]
rel = [e for e in json.load(open(roads_path))["elements"] if e["type"] == "relation"][0]
segs = [[(round(g["lat"] * 1e5), round(g["lon"] * 1e5)) for g in m["geometry"]]
        for m in rel["members"] if m.get("role") == "outer" and m.get("geometry")]
rings = []
while segs:
    ring = segs.pop(0)
    while ring[0] != ring[-1]:
        for i, s in enumerate(segs):
            if s[0] == ring[-1]: ring += s[1:]; break
            if s[-1] == ring[-1]: ring += s[::-1][1:]; break
        else:
            break
        segs.pop(i)
    rings.append(ring)
g = json.load(open(graph_path))
g["boundary"] = [[list(p) for p in r] for r in rings]
g["places"] = {
    "koppel": [52.16207, 5.37778],     # Kleine Koppel 112 (OSM amenity=fire_station)
    "hofslot": [52.19015, 5.40634],    # Het Hofslot 1 (OSM amenity=fire_station)
    "zielhorst": [52.16742, 5.39000],  # Zielhorsterweg x Ringweg-Koppel
    "oost": [52.19665, 5.40560],       # Sportpark Olympus, by Rotonde 1 on Bergenboulevard (approx.)
    "west": [52.19720, 5.39860],       # Sportpark Olympus, west side by Lindeboomseweg (approx.)
}
json.dump(g, open(graph_path, "w"), separators=(",", ":"))
print("rings", [len(r) for r in rings], "closed", [r[0] == r[-1] for r in rings])
