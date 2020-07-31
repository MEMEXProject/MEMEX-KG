#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This sample code

from pymapillary import Mapillary
from pymapillary.utils import *

key = "cHBf9e8n0pG8O0ZVQHGFBQ"

map = Mapillary("insert client id here")
raw_json = map.get_sequence_by_key(key=key)
print(raw_json)

# Download the beautified json for debugging
return_json_file(raw_json, "../sample_json_output/get_sequence_by_key_example.json")
