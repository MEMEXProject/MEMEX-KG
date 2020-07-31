#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This sample code gets a number of resources requested.

from pymapillary import Mapillary
from pymapillary.utils import *

page_num = 1 # What page you want
per_page = 1 # Results per page

map = Mapillary("insert client id here")
raw_json = map.get_pagnation_resources(1, 1)
print(raw_json)

# Download the beautified json for debugging
return_json_file(raw_json, "../sample_json_output/get_pagnation_resources_example.json")
