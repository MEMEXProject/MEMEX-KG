#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This sample code uses a image key to get the image feature.

from pymapillary import Mapillary
from pymapillary.utils import *

key = "LwrHXqFRN_pszCopTKHF_Q"

map = Mapillary("insert client id here")
raw_json = map.get_image_feature_by_key(key=key)
print(raw_json)

# Download the beautified json for debugging
return_json_file(raw_json, "../sample_json_output/get_image_feature_by_key_example.json")
