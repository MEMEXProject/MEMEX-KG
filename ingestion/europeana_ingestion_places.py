"""
-----
Name: europeana_ingestion_places.py
Description:
Loads items from Europeana based on Longitude and Latitude and Location returns a list
to be inserted to Neo4j.
-----
Author: [Stuart James {2}, Hebatallah Mohamed {1}, Sebastiano Vascon {1}]
Licence: 
Copyright: Copyright 2020, MEMEX Project
Credits: [Feliks Hibraj {1}]
Affiliation: {1} Ca'Foscari University of Venice, {2} Istituto Italiano di Tecnologia 
License: BSD
Version: 2.0.0
Last Major Release Date: 31/03/2021
Maintainer: MEMEX Project
Email: contact@memexproject.eu
Status: Dev (Research)
Acknowledgment: 
This project has received funding from the European Union's Horizon 2020
research and innovation programme under grant agreement No 870743.
"""
#import pywikibot
#import pywikibot.data.sparql as spq
import requests
from ingestion.utils import getCityLimitsBoundingBox,valid_latlon
import config as cfg
from math import floor, ceil
from requests.utils import quote
from tqdm import tqdm
import tagme

# Set the authorization token for subsequent calls.
tagme.GCUBE_TOKEN = cfg.europeana["tagme_token"]

def aggregate(url, db_conn, link_to_nodes = False, annotation_threshold=0.1):
    """
    Aggregates cursor to the url and add nodes in the MEMEX-KG
    
    :param url: url
    :param db_conn: database connection
    :param link_to_nodes: a flag to link Europeana nodes to existing nodes in the MEMEX-KG (default FALSE)
    :param annotation_threshold: TAG-ME mandatory threshold
    :return: json items
    """
    data = requests.get(url=url + "&cursor=*")
    res = data.json()["items"]
    last = data.json()
    
    progress_bar = tqdm(total=last["totalResults"])
    
    while 'nextCursor' in last:
        next_cursor = quote(last["nextCursor"])
        data = requests.get(url=url + "&cursor="+ next_cursor)
        last = data.json()
        if "items" in last:
            res = res + last["items"]
            progress_bar.update(len(last["items"]))
        else:
            print("[WARNING] Missing items zero after Cursor")

        dict = get_europeana_dictionary(last["items"])  #convert data in proper dictionary

        # add nodes in the MEMEX-KG
        add_europeana_node(dict, db_conn=db_conn, link_to_nodes=link_to_nodes, annotation_threshold=annotation_threshold)

    return res

def get_europeana_dictionary(result):
    """
    Convert a JSON to dictionary

    :param result: the JSON
    :return: clean_result: the key->value dictionary
    """

    clean_result = []
    for n in result:
        # Rename the id to make Europeana specific
        n["wid"] = "eid_" + n.pop("id")
        for k, v in n.items():
            if isinstance(v, list):
                # Simple but keep first entry
                n[k] = v[0]
            if isinstance(v, dict):
                if "def" in v:
                    if isinstance(v["def"], list):
                        n[k] = v["def"][0]
                    else:
                        n[k] = v["def"]
                # Unknown delete to clean
                n[k] = ""

        # Convert to simpler lat long if exists
        if ("edmPlaceLatitude" in n) and ("edmPlaceLongitude" in n):
            if valid_latlon(float(n["edmPlaceLatitude"]), float(n["edmPlaceLongitude"])):
                n["coordinate_location"] = [float(n["edmPlaceLatitude"]), float(n["edmPlaceLongitude"])]
                del n["edmPlaceLatitude"]
                del n["edmPlaceLongitude"]

        if ("title" in n):
            n["label"] = n["title"]
            del n["title"]

        if ("dcDescription" in n):
            n["description"] = n["dcDescription"]
            del n["dcDescription"]

        if ("edmPreview" in n):
            n["image"] = n["edmPreview"]
            del n["edmPreview"]
            # Keep a simplified version of Europeana (can request if needed)
        key = []
        value = []
        for k, v in n.items():
            key.append(k)
            value.append(v)
        clean_result.append([key, value])

    return clean_result

def add_europeana_node(data, db_conn, link_to_nodes = False, annotation_threshold=0.1):
    """
    Add Europeana nodes into the MEMEX-KG

    :param data: the dictionary of ky->values to be saved in the KG
    :param db_conn: database connection
    :param link_to_nodes: a flag to link Europeana nodes to existing nodes in the MEMEX-KG (default FALSE)
    :param annotation_threshold: TAG-ME mandatory threshold
    """

    wikidata_found = False
    for n in data:
        if link_to_nodes:
            # Add wikidata wids
            wiki_titles = []
            for idx, property_name in enumerate(n[0]):
                if property_name == "label" or property_name == "description" or property_name == "dcCreator":
                    value = n[1][idx]
                    europeana_annotations = tagme.annotate(value)
                    if europeana_annotations:
                        for ann in europeana_annotations.get_annotations(annotation_threshold):
                            t = ann.entity_title
                            t = t[0].lower() + t[1:]
                            wiki_titles.append(t)

            wiki_titles = list(dict.fromkeys(wiki_titles))
            all_wids = []
            for title in wiki_titles:
                wids = db_conn.get_wikidata_ids_by_label(title)
                if wids:
                    all_wids.extend(wids)

            if all_wids:
                wikidata_found = True
                n[0].append("wids")
                n[1].append(all_wids)

        # Insert the node
        db_conn.queue_insert_node(n)  # , additional_class="Europeana")

    # Link to wikidata nodes
    if link_to_nodes and wikidata_found:
        db_conn.match_with_wikidata()

def query_only_id_bboxes(city,db_conn, enlarge=False, link_to_nodes=False, annotation_threshold=0.1):
    """
    Sends a request to openstreetmap to retrieve coordinates of the bounding box of 'city'.
    Divides the area into a regular grid of smaller bounding boxes in order to avoid Timeout for the wikidata query.
    For each grid bounding box call single_bbox_only_id_query(...).
    
    :param city: name of the city to retrieve
    :param enlarge: Looks for a wider area with respect to the city. (Default False)
    :param db_conn: the database connection
    :param link_to_nodes: USe TAGME to add links between existing nodes in the Memex-KG (default False)
    :param annotation_threshold: TAGME threshold (default 0.1)
    :return: list of wikidata entity ids contained in the bounding box of 'city'
    """
    if enlarge:
        top, right, bot, left = getCityLimitsBoundingBox(city,0.3)
    else:
        top, right, bot, left = getCityLimitsBoundingBox(city)
        
    # This currently may end up being larger than the area, however, the API only seems to take integer values (TODO)
    left_most = floor(float(left[0])) -5
    right_most = ceil(float(right[0])) +5
    top_most = ceil(float(top[1])) + 5
    bot_most = floor(float(bot[1])) -5

    # Run a area query based on lat long
    url = 'https://www.europeana.eu/api/v2/search.json?wskey={}&query=pl_wgs84_pos_lat:%5B{}+TO+{}%5D+AND+pl_wgs84_pos_long:%5B{}+TO+{}%5D'.format(cfg.europeana["europeana_token"],left_most,right_most,bot_most,top_most)
    result_lat_lon = aggregate(url, db_conn=db_conn, link_to_nodes=link_to_nodes, annotation_threshold=annotation_threshold)
    print("Found ",len(result_lat_lon), " places")

    # Run area query (broader)
    url = 'https://www.europeana.eu/api/v2/search.json?wskey={}&query=where:{}'.format(cfg.europeana["europeana_token"],city)
    result_city = aggregate(url, db_conn=db_conn, link_to_nodes=link_to_nodes, annotation_threshold=annotation_threshold)
    print("Found ",len(result_city), " knowledge items")

    # Join we let Neo4j handle collisions on id
    # result = result_lat_lon + result_city
    # clean_result = []
    # for n in result:
    #     # Rename the id to make Europeana specific
    #     n["eid"] = "eid" + n.pop("id")
    #     for k, v in n.items():
    #         if isinstance(v,list):
    #             # Simple but keep first entry
    #             n[k] = v[0]
    #         if isinstance(v,dict):
    #             if "def" in v:
    #                 if isinstance(v["def"], list):
    #                     n[k] = v["def"][0]
    #                 else:
    #                     n[k] = v["def"]
    #             # Unknown delete to clean
    #             n[k] = ""
    #
    #     # Convert to simpler lat long if exists
    #     if ("edmPlaceLatitude" in n) and ("edmPlaceLongitude" in n):
    #         if valid_latlon(float(n["edmPlaceLatitude"]),float(n["edmPlaceLongitude"])):
    #             n["coordinate_location"] = [float(n["edmPlaceLatitude"]),float(n["edmPlaceLongitude"]) ]
    #             del n["edmPlaceLatitude"]
    #             del n["edmPlaceLongitude"]
    #
    #     if ("title" in n):
    #         n["label"] = n["title"]
    #         del n["title"]
    #
    #     if ("dcDescription" in n):
    #         n["description"] = n["dcDescription"]
    #         del n["dcDescription"]
    #
    #     if ("edmPreview" in n):
    #         n["image"] = n["edmPreview"]
    #         del n["edmPreview"]
    #     # Keep a simplified version of Europeana (can request if needed)
    #     key = []
    #     value = []
    #     for k, v in n.items():
    #         key.append(k)
    #         value.append(v)
    #     clean_result.append([key,value ])
    #
    # print("Total downloaded ids: ", len(clean_result))

    # return clean_result