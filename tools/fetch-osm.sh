#!/bin/sh
# Downloads Amersfoort road and address data from OpenStreetMap (Overpass API).
# Tries the main server first, then two public mirrors.
cd "$(dirname "$0")"
UA="brandweer-noord-map/0.1 (personal drive-time research)"
SERVERS="https://overpass-api.de/api/interpreter https://overpass.private.coffee/api/interpreter https://maps.mail.ru/osm/tools/overpass/api/interpreter"
for q in roads addresses; do
  for s in $SERVERS; do
    echo "Fetching $q from $s ..."
    curl -sS -A "$UA" -H "Accept: application/json" --data-urlencode "data@$q.overpassql" -o "amersfoort-$q.json" "$s"
    if head -c 20 "amersfoort-$q.json" | grep -q '{'; then echo "  ok"; break; fi
    echo "  failed: $(head -c 200 "amersfoort-$q.json" | tr '\n' ' ')"
  done
done
ls -lh amersfoort-*.json
