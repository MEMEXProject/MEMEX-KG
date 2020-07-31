#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pymapillary import Mapillary
from pymapillary.utils import *
#import cv2
import os
import cv2
import glob

# Create a mappilary object
map = Mapillary("insert client id here")

# Get a sequence. This key was found by going to the site and getting a random
# sequence that seemed short. This sequence has 293 frames
raw_json = map.get_sequence_by_key("nntwXcD2QLuJ_w3dTcXi0Q")

# Download the beautified json for debugging
#return_json_file(raw_json, "result.json")

# Get the image keys value which is a list type
image_keys_json = raw_json['properties']['coordinateProperties']['image_keys']

# Create a images directory
directory = "images"
if not os.path.exists(directory):
    os.makedirs(directory)

# Make shift downloader
count = 0
for image_key in image_keys_json:
    download_image_by_key(image_key, download_path='images/'+ str(count) + ".jpg")
    count +=1

video_name = 'video.avi'
# Get all image file paths
images = [img for img in os.listdir(directory) if img.endswith(".jpg")]

# Sort images in order by file number
# https://stackoverflow.com/questions/33159106/sort-filenames-in-directory-in-ascending-order?lq=1
images.sort(key=lambda f: int(''.join(filter(str.isdigit, f))))

# Get the frame information of one image to use for the video
frame = cv2.imread(os.path.join(directory, images[0]))
height, width, layers = frame.shape
video = cv2.VideoWriter(video_name, 0, 1, (width,height))

# Write video out
for image in images:
    video.write(cv2.imread(os.path.join(directory, image)))
