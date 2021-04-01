"""
-----
Name: db_search.py
Description:
Handles the KG search functionality.
-----
Author: [Diego Pilutti {1}, Hebatallah Mohamed {1}]
Licence: 
Copyright: Copyright 2020, MEMEX Project
Credits: [Sebastiano Vascon {1}, Stuart James {2}]
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
from db.models import get_emb_vect
from db import db_connection

def update_fulltext_index():
    '''
    Drop the search index if exists and create a new one over the entity labels and descriptions.
    '''
    db_conn = db_connection.DB_Connection()
    with db_conn._driver.session() as session:


        try:
            tx = session.begin_transaction()
            tx.run("CALL db.index.fulltext.drop('labelsAndDescriptions')")
            tx.commit()
        except:
            pass

        try:
            tx = session.begin_transaction()
            tx.run("CALL db.index.fulltext.createNodeIndex('labelsAndDescriptions', ['Knowledge', 'Place'], ['label', 'description'])")
            tx.commit()
        except:
            pass
           
def get_within_radius_w2v(tx, long, lat, meters, query):
    '''
    Search for entites using textual embeddings and location information.
    
    :param tx: transaction object reference
    :param long: float type, longitude coordinates
    :param lat: float type, latitude coordinates
    :param meters: integer type, radial distance from point in meters
    :param query: float vector, embedding vector of the text
    :return: list type, list of the records output by Neo4j query
    '''
    wids = []
    result = tx.run("MATCH (p) "
                    "WHERE distance(point({latitude:$lat, longitude:$long}),p.location) < $meters "
                    "AND EXISTS(p.description_w2v) "
                    "RETURN p.label,p.wid,distance(point({latitude:$lat, longitude:$long}),p.location) AS dist, "
                    "gds.alpha.similarity.cosine(p.description_w2v, $query2 ) AS similarity, id(p) "
                    " ORDER BY similarity DESC, dist ASC", lat=lat, long=long, meters=meters, query2=query)
    for record in result:
        wids.append(record)
    return wids


def get_within_radius_fulltext(tx, long, lat, meters, query):
    '''
    Search for entites using fulltext and location information.
        
    :param tx: transaction object reference
    :param long: float type, longitude coordinates
    :param lat: float type, latitude coordinates
    :param meters: integer type, radial distance from point in meters
    :param query: float vector, embedding vector of the text
    :return: list type, list of the records output by Neo4j query
    '''
    wids = []
    
    result = tx.run("CALL db.index.fulltext.queryNodes('labelsAndDescriptions', $query2) YIELD node as p, score as similarity "
                    "WHERE distance(point({latitude:$lat, longitude:$long}),p.location) < $meters "
                    "RETURN p.label,p.wid,distance(point({latitude:$lat, longitude:$long}),p.location) AS dist, similarity "
                    "ORDER BY similarity DESC, dist ASC", lat=lat, long=long, meters=meters, query2=query)
    for record in result:
        wids.append(record)
    return wids


def get_sim_w2v(tx, query):
    '''
    Search for entites using textual embeddings.
    
    :param tx: transaction object reference
    :param query: float vector, embedding vector of the text
    :return: list type, list of the records output by Neo4j query
    '''
    wids = []
    result = tx.run("MATCH (p) "
                    "WHERE EXISTS(p.description_w2v) "
                    "RETURN p.label,p.wid, "
                    "gds.alpha.similarity.cosine(p.description_w2v, $query2 ) AS similarity, id(p) "
                    "ORDER BY similarity DESC", query2=query)
    for record in result:
        wids.append(record)
    return wids


def get_sim_fulltext(tx, query):
    '''
    Search for entites using fulltext.
    
    :param tx: transaction object reference
    :param query: float vector, embedding vector of the text
    :return: list type, list of the records output by Neo4j query
    '''
    wids = []
    result = tx.run("CALL db.index.fulltext.queryNodes('labelsAndDescriptions', $query2) YIELD node as p, score as similarity "
                    "RETURN p.label,p.wid, similarity "
                    "ORDER BY similarity DESC", query2=query)
    for record in result:
        wids.append(record)
    return wids


def get_top_n_closest(search_mode, sentence, n, long, lat, meters):
    '''
    Search for entites using text and location information based on the different search modes (semantic embeddings or fulltext). 
    
    :param search_mode: str type, search mode semantic or fulltext (exact search)
    :param sentence: str type, textual description
    :param n: integer type, subset the top ranked results
    :param long: float type, longitude coordinates
    :param lat: float type, latitude coordinates
    :param meters: integer type, radial distance from point in meters
    :return: list of top n closest points by distance and similarity
    '''
    db_conn = db_connection.DB_Connection()
    if(search_mode == "semantic"):
        prova = [float(x) for x in get_emb_vect(sentence)]

        with db_conn._driver.session() as session:
            wids = session.read_transaction(get_within_radius_w2v, long=long, lat=lat,
                                            meters=meters, query=prova)
    else:
        with db_conn._driver.session() as session:
            wids = session.read_transaction(get_within_radius_fulltext, long=long, lat=lat,
                                            meters=meters, query=sentence)
    db_conn.close()
    return wids[0:n]


def get_top_n_sim(search_mode, sentence, n):
    '''
    Search for entites using text based on the different search modes (semantic embeddings or fulltext). 
    
    :param search_mode: str type, search mode
    :param sentence: str type, textual description
    :param n: integer type, subset the top ranked results
    :return: list of top n closest points by distance and similarity
    '''
    db_conn = db_connection.DB_Connection()
    if(search_mode == "semantic"):
        prova = [float(x) for x in get_emb_vect(sentence)]
         
        with db_conn._driver.session() as session:
            wids = session.read_transaction(get_sim_w2v, query=prova)
    else:
        with db_conn._driver.session() as session:
            wids = session.read_transaction(get_sim_fulltext, query=sentence)
        
    db_conn.close()
    return wids[0:n]


def get_within_radius(tx, long, lat, meters):
    '''
    Search for entites using location information. 
    
    :param tx: transaction object reference
    :param long: float type, longitude coordinates
    :param lat: float type, latitude coordinates
    :param meters: integer type, radial distance from point in meters
    :return: list type, list of the records output by Neo4j query
    '''
    wids = []
    result = tx.run("MATCH (p) "
                    "WHERE distance(point({latitude:$lat, longitude:$long}),p.location) < $meters "
                    "RETURN p.label,p.wid,distance(point({latitude:$lat, longitude:$long}),p.location) AS dist, "
                    " id(p) "
                    "ORDER BY dist ASC", lat=lat, long=long, meters=meters)
    for record in result:
        wids.append(record)
    return wids


def get_top_n_radius(n, long, lat, meters):
    '''
    A wrapper to search for entites using location information. 
    
    :param n: integer type, subset the top ranked results
    :param long: float type, longitude coordinates
    :param lat: float type, latitude coordinates
    :param meters: integer type, radial distance from point in meters
    :return: list of top n closest points by distance and similarity
    '''
    db_conn = db_connection.DB_Connection()
    with db_conn._driver.session() as session:
        wids = session.read_transaction(get_within_radius, long=long, lat=lat,
                                        meters=meters)
    db_conn.close()
    return wids[0:n]
