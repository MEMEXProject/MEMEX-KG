#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This sample code

from pymapillary import Mapillary
from pymapillary.utils import *

# Every parameter example that can be passed in to this search function
# Plug and play as you please
bbox = "16.430300,7.241686,16.438757,7.253186" # minx,miny,maxx,maxy
per_page = 1 # default is 200
userkeys = "HvOINSQU9fhnCQTpm0nN7Q"
usernames = "maning" #example user name

map = Mapillary("insert client id here")
raw_json = map.search_users(userkeys=userkeys, per_page=per_page)
print(raw_json)

# Download the beautified json for debugging
return_json_file(raw_json, "../sample_json_output/search_users_example.json")
