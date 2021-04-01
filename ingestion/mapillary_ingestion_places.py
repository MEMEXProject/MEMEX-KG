"""
-----
Name: mapillary_ingestion_places.py
Description:
Pulls data from Mapillary API based on Longitude and Latitude and Location returns a list
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
from pymapillary import Mapillary
from pymapillary.utils import *
import json
import os.path
from os import path
from ingestion.utils import getCityLimitsBoundingBox
import config as cfg
import time

def latlongdist(center_long,center_lat, img_long,img_lat):
    from math import sin, cos, sqrt, atan2, radians
    # approximate radius of earth in km
    R = 6373.0    

    lat1 = radians(center_lat)
    lon1 = radians(center_long)
    lat2 = radians(img_lat)
    lon2 = radians(img_long)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance

def aggregate(data, link, page_len, map):
    if link==None:
        return data
    res = data
    last = data
    while len(last['features']) == page_len:
        try:
            last,link = map.get_pagnation_resources(link)
        except:
            print("Error incurred, delaying...")
            time.sleep(10)
            last,link = map.get_pagnation_resources(link)
        res['features'] = res['features'] + last['features'] 
        print("Collected ", len(res['features']))
        if link==None:
            break
        time.sleep(2)
    return data


def query_only_id_bboxes(city, enlarge=True):

    # get coordinates of city, request ot open-street-map
    if enlarge:
        top, right, bot, left = getCityLimitsBoundingBox(city,0.3)
    else:
        top, right, bot, left = getCityLimitsBoundingBox(city)
        
    left_most = float(left[0])
    right_most = float(right[0])
    top_most = float(top[1])
    bot_most = float(bot[1])

    # Get the maximum direction and center
    center_lon = (left_most + right_most)/2
    center_lat = (top_most + bot_most)/2
    
    d =latlongdist(left_most,top_most,right_most,bot_most)*1000


    os.makedirs(cfg.mapillary["data_dir"], exist_ok=True)
    city_dir_path = os.path.join(cfg.mapillary["data_dir"],city)
    os.makedirs(city_dir_path , exist_ok=True)
    seq_city_dir_path = os.path.join(city_dir_path, "seq")
    os.makedirs(seq_city_dir_path , exist_ok=True)
    img_city_dir_path = os.path.join(city_dir_path, "img")
    os.makedirs(img_city_dir_path , exist_ok=True)
    imgdata_city_dir_path = os.path.join(city_dir_path, "img_data")
    os.makedirs(imgdata_city_dir_path , exist_ok=True)

    # Create a Mapillary Object
    map = Mapillary(cfg.mapillary["api_key"])
    bbox= str(left_most) + "," + str(bot_most) + "," + str(right_most) + "," +str(top_most)
    if not path.exists(os.path.join(city_dir_path,city+"_result.json")):
        data, next_img = map.search_images(bbox=bbox, per_page=cfg.mapillary["per_page"])
        data = aggregate(data,next_img,cfg.mapillary["per_page"],map)
        # Download the beautified json for debugging
        return_json_file(data, os.path.join(city_dir_path,city+"_result.json"))
    else:
        data = json.load(open(os.path.join(city_dir_path,city+"_result.json")))

    nodes = []
    
    for idx,f in enumerate(data["features"]):
        if not 'sequence_key' in f["properties"]:
            print('Skip ', str(idx),'/',len(data["features"]))
            continue
        print('Processing ', str(idx),'/',len(data["features"]) ,' - ', f["properties"]["sequence_key"])

        seq_raw_path = os.path.join(seq_city_dir_path, f["properties"]["sequence_key"] + ".json")
        if not path.exists(seq_raw_path):
            try:
                print('Pulling ', str(idx),'/',len(data["features"]) ,' - ', f["properties"]["sequence_key"])
                seq_raw_json = map.get_sequence_by_key(key=f["properties"]["sequence_key"])
            except:
                print('Failed to acuire, skipping')
                continue
            return_json_file(seq_raw_json, seq_raw_path)
        else:
            print('Loading ', str(idx),'/',len(data["features"]) ,' - ', f["properties"]["sequence_key"])
            seq_raw_json = json.load(open(seq_raw_path))

        for i, img_id in enumerate(seq_raw_json["properties"]["coordinateProperties"]["image_keys"]):
            
            # Check is in target area
            lon,lat = seq_raw_json["geometry"]["coordinates"][i]
        
            img_path = os.path.join(img_city_dir_path, img_id + ".jpg")
            img_data_path = os.path.join(imgdata_city_dir_path, img_id + ".json")
            if not path.exists(img_path):
                print(' Pulling',img_id)
                download_image_by_key(img_id,2048,img_path)
            if not path.exists(img_data_path):
                # Organise a custom Json to massively redundant but abstracts sequences
                img_data = {}
                img_data["coordinate_location"] = seq_raw_json["geometry"]["coordinates"][i]
                img_data["file_path"] = img_path
                img_data["image_key"] = img_id
                img_data["camera_make"] = seq_raw_json["properties"]["camera_make"]
                img_data["captured_at"] = seq_raw_json["properties"]["captured_at"]
                img_data["created_at"] = seq_raw_json["properties"]["created_at"]
                img_data["pano"] = seq_raw_json["properties"]["pano"]
                img_data["user_key"] = seq_raw_json["properties"]["user_key"]
                img_data["username"] = seq_raw_json["properties"]["username"]
                img_data["cas"] = seq_raw_json["properties"]["coordinateProperties"]["cas"][i]
                
                with open(img_data_path, "w") as write_file:
                    json.dump(img_data ,write_file,indent=2)
            else:
                img_data = json.load(open(img_data_path))
            # Add to Knowledge Graph
            keys = []
            values = []
            for k,v in img_data.items():
                keys.append(k)
                values.append(v)
            nodes.append( [keys,values])

    return nodes

