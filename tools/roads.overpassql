[out:json][timeout:300];
way["highway"~"^(motorway|motorway_link|trunk|trunk_link|primary|primary_link|secondary|secondary_link|tertiary|tertiary_link|unclassified|residential|living_street|service|road|busway)$"](52.08,5.25,52.24,5.54)->.r;
.r out body qt;
.r >; out skel qt;
rel["boundary"="administrative"]["admin_level"="8"]["name"="Amersfoort"]; out geom qt;
