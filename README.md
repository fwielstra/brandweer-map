# Amersfoort opkomstkaart

An interactive map that estimates how quickly a fire engine can reach every street in
Amersfoort from one or more fire stations. Place or drag station pins on the map and
every road is coloured from blue (fast) to red (slow) by the estimated
*opkomsttijd*: the time from the emergency call until the first fire engine arrives.

## What you can do with it

- Drag stations around, add new ones, and switch them between a professional crew
  (short turn-out time) and volunteers (longer turn-out time).
- Colour roads by time, by response-time norm (good, sufficient, insufficient),
  or by which station gets there first.
- See the share of addresses reached in time, north and south of the A1, as a
  curve you can compare against a saved baseline.
- Search the whole city for station locations that reach the most addresses
  within a chosen time.

## How the times are estimated

Opkomsttijd = dispatch time + turn-out time + driving time.

- Driving time is computed in the browser over the OpenStreetMap road network,
  assuming no traffic and no traffic lights. Road speeds come from road type and
  speed limit.
- Default turn-out and dispatch times, and the speed settings, were tuned so that
  the map reproduces response-time figures the regional fire service has published.
  All of them can be changed on the page.
- Each address is linked to its nearest road, and counted as reached when the
  fire engine gets to that point of the road.

## Disclaimer

This is an independent hobby project. It is not affiliated with or endorsed by any
fire service, safety region or municipality.

The map is built from public data and simplified assumptions. Its results are rough
estimates. They are not a scientific study, not a legal assessment, and not
legally binding, and they should not be used as the basis for conclusions,
decisions or claims about emergency response. Real response times depend on many
things this model leaves out, such as traffic, weather, crew availability and the
exact routes fire engines take.

**This project, including all code and this README, was written entirely by an AI
assistant (Claude, by Anthropic)**, with direction from the repository owner. It has
not been reviewed by fire service professionals.

## Running it

The site is static: an HTML page, a data file and fonts. To run it locally:

```sh
python3 -m http.server 8000
# then open http://localhost:8000
```

Opening `index.html` directly from disk does not work, because browsers block
loading the data file from `file://` URLs.

To publish it on GitHub Pages, go to the repository's Settings, then Pages, and
choose "Deploy from a branch" with the `main` branch and the `/ (root)` folder.

## Updating the road data

```sh
tools/fetch-osm.sh   # downloads roads and addresses from the Overpass API (about 40 MB)
tools/build.sh       # builds data/amersfoort-graph.json from them
```

Station positions are set in `tools/augment.py`. Needs Python 3 and curl, with no
extra packages.

## Files

- `index.html`: the whole application (map drawing, route search, interface).
- `data/amersfoort-graph.json`: the road network and addresses in a compact form.
- `fonts/`: self-hosted web fonts, so the page loads no third-party fonts.
- `tools/`: scripts that download and convert OpenStreetMap data.

## Credits and licences

- Code: MIT License, see `LICENSE`.
- Road and address data: © [OpenStreetMap](https://www.openstreetmap.org/copyright)
  contributors, available under the Open Database License (ODbL).
  `data/amersfoort-graph.json` is a derived database and is released under the
  ODbL as well.
- Background map tiles: © OpenStreetMap contributors, served by the OpenStreetMap
  Foundation under its [tile usage policy](https://operations.osmfoundation.org/policies/tiles/).
  That service is meant for light use. If this site gets heavy traffic, switch to a
  commercial or self-hosted tile provider.
- Fonts: Barlow Semi Condensed, Source Sans 3 and IBM Plex Mono, all under the
  SIL Open Font License 1.1 (see `fonts/`).
