#!/bin/sh
# Turns the raw OpenStreetMap downloads into data/amersfoort-graph.json.
# Run tools/fetch-osm.sh first. Needs Python 3, no extra packages.
set -e
cd "$(dirname "$0")"
python3 -I build_data.py amersfoort-roads.json amersfoort-addresses.json ../data/amersfoort-graph.json
python3 -I augment.py amersfoort-roads.json ../data/amersfoort-graph.json
ls -lh ../data/amersfoort-graph.json
