#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This example uses the function search_images to do a query based
# on the variables that are declared below.

from pymapillary import Mapillary
from pymapillary.utils import *

# Every parameter that can be passed in to this search function
# Plug and play as you please
bbox = "16.430300,7.241686,16.438757,7.253186" # minx,miny,maxx,maxy
closeto = "13.0006076843,55.6089295863" #longitude, latitude
end_time = "2016-03-14T13:44:37.206Z" #must be a valid ISO 8601 date
image_keys = "LwrHXqFRN_pszCopTKHF_Q, Aufjv2hdCKwg9LySWWVSwg"
lookat= "12.9981086701,55.6075236275" #longitude, latitude
pano = "true" # or "false" it has to be lower cased
per_page = 1 # default is 200
project_keys="HvOINSQU9fhnCQTpm0nN7Q" #json is userkey this worked too? PSaXX2JB7snjFyHJF-Rb1A for sequence key? JnLaPNIam8LFNZL1Zh9bPQ all keys work?
radius=100 # In meters
sequence_keys="PSaXX2JB7snjFyHJF-Rb1A, LMlIPUNhaj24h_q9v4ArNw"
start_time = "2016-03-14T13:44:37.206Z" #start_time" must be a valid ISO 8601 date
userkeys = "HvOINSQU9fhnCQTpm0nN7Q"
usernames = "maning" #example user name

# Create a Mapillary Object
map = Mapillary("insert client id here")
raw_json = map.search_images(bbox=bbox, per_page=per_page)
print(raw_json)

# Download the beautified json for debugging
return_json_file(raw_json, "../sample_json_output/search_images_example.json")
