#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import wget
import os
import json

# https://www.mapillary.com/developer/api-documentation/#retrieve-image-sources
def download_image_by_key(key, image_resolution=320, download_path=None):

    """Download a image by the key

    Args:
        key (string): Image key of the image you want to download.
        image_resolution (int): Resolution of the image you want to download.
        download_path (string): The download path of the file to download.

    Return:
        (boolean): True if the download is sucessful (for now)

    """

    # Check the image_resolution argument and create the url to download
    if image_resolution == 320:
        url = "https://d1cuyjsrcm0gby.cloudfront.net" + "/" + key + "/thumb-320.jpg"
    elif image_resolution == 640:
        url = "https://d1cuyjsrcm0gby.cloudfront.net" + "/" + key + "/thumb-640.jpg"
    elif image_resolution == 1024:
        url = "https://d1cuyjsrcm0gby.cloudfront.net" + "/" + key + "/thumb-1024.jpg"
    elif image_resolution == 2048:
        url = "https://d1cuyjsrcm0gby.cloudfront.net" + "/" + key + "/thumb-2048.jpg"

    # Use the wget library to download the url
    filename = wget.download(url, download_path)

    return True

def return_json_file(raw_json, file_name):

    """Returns nicely formated json file as .json. Used for debugging.

    Args:
        param raw_json(dict):    Takes in a json dict.
        param file_name(string): Name of the file name you want to write too.

    Return:
        True (boolean):          Return True if the function finished properly
                                 (for now)
    """

    # Open file with the ability to write to the file
    with open(file_name, "w") as data_file:
        json.dump(raw_json, data_file, indent=4, sort_keys=True)

    return True
