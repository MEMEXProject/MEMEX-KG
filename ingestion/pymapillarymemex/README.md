# branch of pymapillary
Original Repository at: https://github.com/khmurakami/pymapillary

# Orignal Documentation:

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://travis-ci.com/khmurakami/pymapillary.svg?token=GdqQUUu1xsypr1oorMoh&branch=master)](https://travis-ci.com/khmurakami/pymapillary)
[![CodeFactor](https://www.codefactor.io/repository/github/khmurakami/pymapillary/badge)](https://www.codefactor.io/repository/github/khmurakami/pymapillary)
![GitHub All Releases](https://img.shields.io/github/downloads/khmurakami/pymapillary/total.svg)
[![HitCount](http://hits.dwyl.com/khmurakami/pymapillary.svg)](http://hits.dwyl.com/khmurakami/pymapillary)

Python Wrapper for Mapillary API V3

## Requirements

Also listed in requirements.txt:

- requests==2.21.0
- wget==3.2

Optional dependencies for sample application

- opencv-python==4.0.0.21
- glob3==0.0.1

## Install

#### Install Locally

This was only tested in Python 3.6

```shell
$ python3 setup.py install
```

#### Install inside a virtualenv
```shell
$ pip3 install virtualenv
$ python3 -m virutalenv env
$ source env/bin/activate
$ python3 setup.py install
```

## Using the Python Wrapper

Descriptions of functions can be found inside pymapillary/pymapillary.py

Sample examples can be found in examples_code/python_scripts

Search by images with search_images():
```python
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
map = Mapillary("insert client key here")
raw_json = map.search_images(bbox=bbox, per_page=per_page)
print(raw_json)

# Download the beautified json for debugging
return_json_file(raw_json, "result.json")
```

Response:
```json
{
    "features": [
        {
            "geometry": {
                "coordinates": [
                    16.432976,
                    7.249027
                ],
                "type": "Point"
            },
            "properties": {
                "ca": 329.94820000000004,
                "camera_make": "Apple",
                "camera_model": "iPhone5,4",
                "captured_at": "2016-03-14T13:45:45.849Z",
                "key": "G_SIwxNcioYeutZuA8Rurw",
                "pano": false,
                "sequence_key": "LMlIPUNhaj24h_q9v4ArNw",
                "user_key": "AGfe-07BEJX0-kxpu9J3rA",
                "username": "pierregeo"
            },
            "type": "Feature"
        }
    ],
    "type": "FeatureCollection"
}
```

## Samples

Code samples can be found in example_code

### Download a image by image key


```python
# This sample code downloads an image by the image key used in the
# API documentation. It downloads a jpg to whatever file this was
# executed from. It downloads a 1024 image.

from utils import *

download_image_by_key("LwrHXqFRN_pszCopTKHF_Q", 1024. '/image.jpg')
```

### Create a video from a sequence result

This gif shows a sample part of a video created from using a sequence key to get a list of image keys. Then using cv2 and glob to create the video. To run the application you need to install cv2 and glob. The sample application can be found in example_code/sample_applications

Install Dependencies
```shell
$ pip install opencv-python
$ pip install glob3
```

Run application
```shell
$ python create_video_from_sequence.py
```

Result

![Alt Text](example_code/sample_applications/result.gif)

## Testing using Unit Tests

Run test script to test if it works properly

```shell
$ python unit_test/pymapillary_tests.py
```

## Using Curl Requests to Test

These curl requests are from the Mapillary and are not mine. They can be found here: <https://www.mapillary.com/developer/api-documentation/#introduction>

```
$ cd example_curl_requests
$ ./pagnation_example.sh
```

## Notes

- search_image_detections is not tested because I don't have access to it
- search_map_features is not tested because I don't have access to it


## TODO

- Have example parsing json
- Make README.md better
- create upload function
- add support for gpx format
