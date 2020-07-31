"""
-----
Name: europeana_ingestion_places.py
Description:
Loads items from Europeana based on Longitude and Latitude and Location returns a list
to be inserted to Neo4j.
-----
Author: Stuart James {2}
Licence: 
Copyright: Copyright 2020, MEMEX Project
Credits: [Sebastiano Vason {1}, Feliks Hibraj {1}]
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
import pywikibot
import pywikibot.data.sparql as spq
import requests
from ingestion.utils import getCityLimitsBoundingBox,valid_latlon
import config as cfg
from math import floor, ceil


def aggregate(url):
    data = requests.get(url=url + "&cursor=*")
    res = data.json()["items"]
    last = data.json()
    
    while 'nextCursor' in last:
        data = requests.get(url=url + "&cursor="+  last['nextCursor'])
        last = data.json()
        if "items" in last:
            res = res + last["items"]
        else:
            print("[WARNING] Missing items zero after Cursor")
        last =data.json()
    return res


def query_only_id_bboxes(city,enlarge=False):
    """
    Sends a request to openstreetmap to retrieve coordinates of the bounding box of 'city'.
    Divides the area into a regular grid of smaller bounding boxes in order to avoid Timeout for the wikidata query.
    For each grid bounding box call single_bbox_only_id_query(...).
    
    :param city: name of the city to retrieve 
    :return: list of wikidata entity ids contained in the bounding box of 'city'
    """
    if enlarge:
        top, right, bot, left = getCityLimitsBoundingBox(city,0.3)
    else:
        top, right, bot, left = getCityLimitsBoundingBox(city)
        
    # This currently may end up being larger than the area, however, the API only seems to take integer values (TODO)
    left_most = floor(float(left[0]))
    right_most = ceil(float(right[0]))
    top_most = ceil(float(top[1]))
    bot_most = floor(float(bot[1]))

    # Run a area query based on lat long
    url = 'https://www.europeana.eu/api/v2/search.json?wskey={}&query=pl_wgs84_pos_lat:%5B{}+TO+{}%5D+AND+pl_wgs84_pos_long:%5B{}+TO+{}%5D'.format(cfg.europeana["token"],left_most,right_most,bot_most,top_most)
    result_lat_lon = aggregate(url)
    print("Found ",len(result_lat_lon), " places")
    # Run area query (broader)
    url = 'https://www.europeana.eu/api/v2/search.json?wskey={}&query=where:{}'.format(cfg.europeana["token"],city)
    result_city  = aggregate(url)
    print("Found ",len(result_city), " knowledge items")
    # Join we let Neo4j handle collisions on id
    result = result_lat_lon + result_city
    clean_result = []
    for n in result:
        # Rename the id to make Europeana specific
        n["eid"] = "eid" + n.pop("id")
        for k, v in n.items():
            if isinstance(v,list):
                # Simple but keep first entry
                n[k] = v[0]
            if isinstance(v,dict):
                if "def" in v:
                    if isinstance(v["def"], list):
                        n[k] = v["def"][0]
                    else:
                        n[k] = v["def"]
                # Unknown delete to clean
                n[k] = ""

        # Convert to simpler lat long if exists
        if ("edmPlaceLatitude" in n) and ("edmPlaceLongitude" in n):
            if valid_latlon(float(n["edmPlaceLatitude"]),float(n["edmPlaceLongitude"])):
                n["coordinate_location"] = [float(n["edmPlaceLatitude"]),float(n["edmPlaceLongitude"]) ]
                del n["edmPlaceLatitude"]
                del n["edmPlaceLongitude"]
        # Keep a simplified version of Europeana (can request if needed)
        key = []
        value = []
        for k, v in n.items():
            key.append(k)
            value.append(v)
        clean_result.append([key,value ])
        
    print("Total downloaded ids: ", len(clean_result))

    return clean_result
