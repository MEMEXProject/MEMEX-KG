#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This sample code

from pymapillary import Mapillary
from pymapillary.utils import *

# Every parameter that can be passed in to this search function
# Plug and play as you please
bbox = "16.430300,7.241686,16.438757,7.253186" # minx,miny,maxx,maxy
end_time = "2016-03-14T13:44:37.206Z" #must be a valid ISO 8601 date
iso_countries = "SE" # given as ISO 3166 country codes.
per_page = 1 # default is 200
start_time = "2016-03-14T13:44:37.206Z" #start_time" must be a valid ISO 8601 date
userkeys = "AGfe-07BEJX0-kxpu9J3rA"
usernames = "maning" #example user name

map = Mapillary("insert client id here")
raw_json = map.filter_image_upload_lboards(iso_countries=iso_countries, per_page=per_page)
print(raw_json)

# Download the beautified json for debugging
return_json_file(raw_json, "../sample_json_output/filter_image_upload_lboards_example.json")
