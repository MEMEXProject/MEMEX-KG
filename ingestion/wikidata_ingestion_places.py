
"""
-----
Name: wikidata_ingestion_places.py
Description:
Pulls data from Wikidata API based on Longitude and Latitude and Location returns a list
to be inserted to Neo4j.
-----
Author: Feliks Hibraj {1}
Licence: 
Copyright: Copyright 2020, MEMEX Project
Credits: [Sebastiano Vascon {1}, Stuart James {2}]
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
from ingestion.utils import getCityLimitsBoundingBox

def single_bbox_only_id_query(sw_x, sw_y, ne_x, ne_y):
    """
    Retrieves a list of wikidata entity ids contained on the specified bounding box.
    
    :param sw_x: South-West x coordinate
    :param sw_y: South-West y coordinate
    :param ne_x: North-East x coordinate
    :param ne_y: North-East y coordinate
    :return: list of wikidata entity ids contained on the specified bounding box
    """
    query = f"""
    SELECT ?place
    WHERE{{
        SERVICE wikibase:box {{
            ?place wdt:P625 ?location . 
            bd:serviceParam wikibase:cornerSouthWest "Point({sw_x} {sw_y})"^^geo:wktLiteral.
            bd:serviceParam wikibase:cornerNorthEast "Point({ne_x} {ne_y})"^^geo:wktLiteral.
        }}
    }}
    """
    print('Run box:',sw_x, sw_y, ne_x, ne_y)
    wikidata_site = pywikibot.Site("wikidata", "wikidata")
    query_object = spq.SparqlQuery(repo=wikidata_site)
    data = query_object.select(query)  # returns a list, where data[0] is the first item,
    return data


def query_only_id_bboxes(city, enlarge=False):
    """
    Sends a request to openstreetmap to retrieve coordinates of the bounding box of 'city'.
    Divides the area into a regular grid of smaller bounding boxes in order to avoid Timeout for the wikidata query.
    For each grid bounding box call single_bbox_only_id_query(...).
    
    :param city: name of the city to retrieve 
    :return: list of wikidata entity ids contained in the bounding box of 'city'
    """
    # get coordinates of city, request ot open-street-map
    if enlarge:
        top, right, bot, left = getCityLimitsBoundingBox(city,0.3)
    else:
        top, right, bot, left = getCityLimitsBoundingBox(city)
        
    left_most = float(left[0])
    right_most = float(right[0])
    top_most = float(top[1])
    bot_most = float(bot[1])

    # print("left {}, right {}, top {}, bottom {}".format(left_most, right_most, top_most, bot_most))
    n_steps_x = 6
    n_steps_y = 6
    x_step = abs(left_most-right_most)/n_steps_x
    y_step = abs(top_most-bot_most)/n_steps_y

    x = [left_most]
    tmp = left_most
    for _ in range(n_steps_x):
        tmp += x_step
        x.append(tmp)
    y = [bot_most]
    tmp = bot_most
    for _ in range(n_steps_y):
        tmp += y_step
        y.append(tmp)

    nr_results = 0
    # now we have a grid of coordinates, have to loop on all 16 bboxes
    result = []
    for x_ in range(n_steps_x):
        for y_ in range(n_steps_y):
            sw_x = x[x_]
            sw_y = y[y_]
            ne_x = x[x_+1]
            ne_y = y[y_+1]
            data = single_bbox_only_id_query(sw_x, sw_y, ne_x, ne_y)
            result.extend(data)
            nr_results += len(data)
    print("Total downloaded ids: ", nr_results)
    return result
