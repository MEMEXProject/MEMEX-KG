#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This sample code uses a changeset key to get a changeset

from pymapillary import Mapillary
from pymapillary.utils import *

key = "obWjkY7TGbstLRNy1qYRD7"

map = Mapillary("insert client id here")
raw_json = map.get_changeset_by_key(key=key)
print(raw_json)

# Download the beautified json for debugging
return_json_file(raw_json, "../sample_json_output/get_changeset_by_key_example.json")
