"""
-----
Name: utils.py
Description:
Provides utility functions to other files including:
- getCityLimitsBoundingBox to retrieve from Open Street Map the limits of a city
- str2bool convert command line argumnts to bools
-----
Author: Feliks Hibraj {1}
Licence: 
Copyright: Copyright 2020, MEMEX Project
Credits: [Sebastiano Vason {1}, Stuart James {2}]
Affiliation: {1} Ca'Foscari University of Venice, {2} Istituto Italiano di Tecnologia 
License: BSD
Version: 1.0.0
Last Major Release Date: 31/07/2020
Maintainer: MEMEX Project
Email: contact@memexproject.eu
Status: Dev (Research)
Acknowledgment: 
This project has received funding from the European Union's Horizon 2020
research and innovation programme under grant agreement No 870743.
"""
import requests

def getCityLimitsBoundingBox(city, expandBy=0.0):
    """
    Retrieve from Open Street Map the limits of a city
    :param city: name of city
    :param expandBy: percentage to enlage the region
    :return: bounding box for the city limits
    """
    url = "https://nominatim.openstreetmap.org/search?city={}&format=json&addressdetails=1&limit=1".format(city)
    r = requests.get(url=url)
    bbox_coords = r.json()[0]['boundingbox']
    top = [float(bbox_coords[3]), float(bbox_coords[1])]
    right = top
    bot = [float(bbox_coords[2]), float(bbox_coords[0])]
    left = bot

    # enlarge bounding box in order to include the entire neighborhood of the respectve pilot 
    if expandBy > 0.0:
        diff_y = top[1]-bot[1]
        top[1] = top[1]+(diff_y*expandBy)
        bot[1] = bot[1]-(diff_y*expandBy)
        diff_x = left[0]-right[0]
        right[0] = right[0]+(diff_x*expandBy)
        left[0] = left[0]-(diff_x*expandBy)
    return top, right, bot, left


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def valid_latlon(lat, long):
    if (lat >= -90) and (lat <= 90) and (long >= -180) and (long <= 180):
        return True
    return False