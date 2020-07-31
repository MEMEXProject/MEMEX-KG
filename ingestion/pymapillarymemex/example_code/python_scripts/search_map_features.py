#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This sample code get map features detections. I can't really test it because
# I don't have access to it.

from pymapillary import Mapillary
from pymapillary.utils import *

layers = "trafficsigns"

map = Mapillary("insert client id here")
raw_json = map.search_map_features(layers=layers)
print(raw_json)

# Download the beautified json for debugging
return_json_file(raw_json, "../sample_json_output/search_map_features_example.json")
