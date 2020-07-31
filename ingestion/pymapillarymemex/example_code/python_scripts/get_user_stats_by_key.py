#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This sample code

from pymapillary import Mapillary
from pymapillary.utils import *

key = "2BJl04nvnfW1y2GNaj7x5w"

map = Mapillary("insert client id here")
raw_json = map.get_user_stats_by_key(key=key)
print(raw_json)

# Download the beautified json for debugging
return_json_file(raw_json, "../sample_json_output/get_user_stats_by_key_example.json")
