"""
-----
Name: db_search.py
Description:
Handles the KG search functionality.
-----
Author: [Hebatallah Mohamed {1}, Diego Pilutti {1}]
Licence: 
Copyright: Copyright 2020, MEMEX Project
Credits: [Sebastiano Vascon {1}, Stuart James {2}]
Affiliation: {1} Ca'Foscari University of Venice, {2} Istituto Italiano di Tecnologia 
License: BSD
Version: 3.0.0
Last Major Release Date: 31/05/2021
Maintainer: MEMEX Project
Email: contact@memexproject.eu
Status: Dev (Research)
Acknowledgment: 
This project has received funding from the European Union's Horizon 2020
research and innovation programme under grant agreement No 870743.
"""
from db.models import get_emb_vect
from db import db_connection

def update_fulltext_index(lang = "en"):
    '''
    Drop the search index if exists and create a new one over the entity labels and descriptions.
    
    :param lang: language to return
    '''
    if lang == "en":
        lang = ""
    else:  
        lang = "_" + lang
        
    db_conn = db_connection.DB_Connection()
    with db_conn._driver.session() as session:
        try:
            tx = session.begin_transaction()
            tx.run("CALL db.index.fulltext.drop('labelsAndDescriptions')")
            tx.commit()
        except:
            pass
    with db_conn._driver.session() as session:
        try:
            tx = session.begin_transaction()
            tx.run("CALL db.index.fulltext.createNodeIndex('labelsAndDescriptions', ['Knowledge', 'Place'], ['label"+lang+"', 'description"+lang+"'])")
            tx.commit()
        except:
            pass
        
def update_named_graph():
    '''
    Drop the named graph if exists and create a new one over "Place" and "Knowledge" nodes.
    '''
    db_conn = db_connection.DB_Connection()
    with db_conn._driver.session() as session:
        try:
            tx = session.begin_transaction()
            tx.run("CALL gds.graph.drop('memex-graph')")
            tx.commit()
        except:
            pass 
    with db_conn._driver.session() as session:
        try:
            tx = session.begin_transaction()
            tx.run("CALL gds.graph.create('memex-graph',['Place', 'Knowledge'],'*')")
            tx.commit()
        except:
            pass 
        
def get_within_radius_w2v(tx, long, lat, meters, query, lang = "en"):
    '''
    Search for entites using textual embeddings and location information.
    
    :param tx: transaction object reference
    :param long: float type, longitude coordinates
    :param lat: float type, latitude coordinates
    :param meters: integer type, radial distance from point in meters
    :param query: float vector, embedding vector of the text
    :param lang: language to return
    :return: list type, list of the records output by Neo4j query
    '''
    if lang == "en":
        lang = ""
    else:  
        lang = "_" + lang   
    results = []
    result = tx.run("MATCH (p) "
                    "WHERE distance(point({latitude:$lat, longitude:$long}),p.location) < $meters "
                    "AND EXISTS(p.description_w2v) "
                    "RETURN p.label_"+lang+",p.wid,distance(point({latitude:$lat, longitude:$long}),p.location) AS dist, "
                    "gds.alpha.similarity.cosine(p.description_w2v, $query2 ) AS similarity, id(p) "
                    "ORDER BY similarity DESC, dist ASC", lat=lat, long=long, meters=meters, query2=query)
    for record in result:
        results.append(record)
    return results

def get_visual(tx, query, lang = "en"):
    '''
    Search for entites using textual embeddings and location information.
    
    :param tx: transaction object reference
    :param long: float type, longitude coordinates
    :param lat: float type, latitude coordinates
    :param meters: integer type, radial distance from point in meters
    :param query: float vector, embedding vector of the text
    :param lang: language to return
    :return: list type, list of the records output by Neo4j query
    '''
    results = []
    if lang == "en":
        lang = ""
    else:  
        lang = "_" + lang
    result = tx.run("MATCH (p) "
                    "WHERE EXISTS(p.image_emb) "
                    "RETURN p.label"+lang+" as label,p.wid as wid,p.image as image_url,p.location as location,p.description"+lang + " as description, "
                    "gds.alpha.similarity.euclideanDistance(p.image_emb, $query2 ) AS similarity, id(p) "
                    " ORDER BY similarity ASC", query2=query)
    for record in result:
        results.append(record)
    return results

def get_within_radius_visual(tx, long, lat, meters, query, lang = "en"):
    '''
    Search for entites using textual embeddings and location information.
    
    :param tx: transaction object reference
    :param long: float type, longitude coordinates
    :param lat: float type, latitude coordinates
    :param meters: integer type, radial distance from point in meters
    :param query: float vector, embedding vector of the text
    :param lang: language to return
    :return: list type, list of the records output by Neo4j query
    '''
    results = []
    if lang == "en":
        lang = ""
    else:  
        lang = "_" + lang
    result = tx.run("MATCH (p) "
                    "WHERE distance(point({latitude:$lat, longitude:$long}),p.location) < $meters "
                    "AND EXISTS(p.image_emb) "
                    "RETURN p.label"+lang+" as label,p.wid as wid,p.image as image_url,p.description"+lang + " as description,p.location as location, distance(point({latitude:$lat, longitude:$long}),p.location) AS dist, "
                    "gds.alpha.similarity.euclideanDistance(p.image_emb, $query2 ) AS similarity, id(p) "
                    " ORDER BY similarity ASC, dist ASC", lat=lat, long=long, meters=meters, query2=query)
    for record in result:
        results.append(record)
    return results

def get_within_radius_fulltext(tx, long, lat, meters, query, lang = "en"):
    '''
    Search for entites using fulltext and location information.
        
    :param tx: transaction object reference
    :param long: float type, longitude coordinates
    :param lat: float type, latitude coordinates
    :param meters: integer type, radial distance from point in meters
    :param query: float vector, embedding vector of the text
    :param lang: language to return
    :return: list type, list of the records output by Neo4j query
    '''
    if lang == "en":
        lang = ""
    else:  
        lang = "_" + lang   
    results = []
    result = tx.run("CALL db.index.fulltext.queryNodes('labelsAndDescriptions', $query2) YIELD node as p, score as similarity "
                    "WHERE distance(point({latitude:$lat, longitude:$long}),p.location) < $meters "
                    "RETURN p.label_"+lang+",p.wid,distance(point({latitude:$lat, longitude:$long}),p.location) AS dist, similarity, id(p) "
                    "ORDER BY similarity DESC, dist ASC", lat=lat, long=long, meters=meters, query2=query)
    for record in result:
        results.append(record)
    return results


def get_sim_w2v(tx, query):
    '''
    Search for entites using textual embeddings.
    
    :param tx: transaction object reference
    :param query: float vector, embedding vector of the text
    :return: list type, list of the records output by Neo4j query
    '''
    results = []
    result = tx.run("MATCH (p) "
                    "WHERE EXISTS(p.description_w2v) "
                    "RETURN p.label, p.wid, "
                    "gds.alpha.similarity.cosine(p.description_w2v, $query2) AS similarity, id(p) "
                    "ORDER BY similarity DESC", query2=query)
    for record in result:
        results.append(record)
    return results


def get_sim_fulltext(tx, query):
    '''
    Search for entites using fulltext.
    
    :param tx: transaction object reference
    :param query: float vector, embedding vector of the text
    :return: list type, list of the records output by Neo4j query
    '''
    results = []
    result = tx.run("CALL db.index.fulltext.queryNodes('labelsAndDescriptions', $query2) YIELD node as p, score as similarity "
                    "RETURN p.label, p.wid, similarity, id(p) "
                    "ORDER BY similarity DESC", query2=query)
    for record in result:
        results.append(record)
    return results


def get_top_similar_closest(search_mode, sentence, n, long, lat, meters):
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
            results = session.read_transaction(get_within_radius_w2v, long=long, lat=lat,
                                            meters=meters, query=prova)
    else:
        with db_conn._driver.session() as session:
            results = session.read_transaction(get_within_radius_fulltext, long=long, lat=lat,
                                            meters=meters, query=sentence)
    return results[:n]


def get_top_similar(search_mode, sentence, n):
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
            results = session.read_transaction(get_sim_w2v, query=prova)
    else:
        with db_conn._driver.session() as session:
            results = session.read_transaction(get_sim_fulltext, query=sentence)
    return results[:n]


def get_top_closest(tx, n, long, lat, meters, lang="en"):
    '''
    Search for entites using location information. 
    
    :param tx: transaction object reference
    :param n: integer type, number of records
    :param long: float type, longitude coordinates
    :param lat: float type, latitude coordinates
    :param meters: integer type, radial distance from point in meters
    :param lang: language to return
    :return: list type, list of the records output by Neo4j query
    '''
    if lang == "en":
        lang = ""
    else:  
        lang = "_" + lang   
    results = []
    db_conn = db_connection.DB_Connection()
    with db_conn._driver.session() as session:
        tx = session.begin_transaction()
        result = tx.run("MATCH (p) "
                        "WHERE distance(point({latitude:$lat, longitude:$long}),p.location) < $meters "
                        "RETURN p.label_"+lang+",p.wid,distance(point({latitude:$lat, longitude:$long}),p.location) AS dist, "
                        " id(p) "
                        "ORDER BY dist ASC LIMIT $n", lat=lat, long=long, meters=meters, n=n)
        for record in result:
            results.append(record)
        return results

    
def get_top_ppr(ppr_seed, max_num=10, lang="en"):
    '''
    Get nodes based on Personalized PageRank(PPR).
    
    :param ppr_seed: PPR seed node ID.
    :param max_num: maximum number of records to retrieve.
    :param lang: language to return
    :return: list type, list of the records output by Neo4j query
    '''    
    if lang == "en":
        lang = ""
    else:  
        lang = "_" + lang   
        
    results = []
    db_conn = db_connection.DB_Connection()
    with db_conn._driver.session() as session:
        tx = session.begin_transaction()
        ppr_result = tx.run(f"MATCH (p) WHERE ID(p) = {ppr_seed} "
                            "WITH p CALL gds.pageRank.stream('memex-graph', { maxIterations: 10, dampingFactor: 0.85, sourceNodes: [p] }) YIELD nodeId, score AS pageRank "
                            "RETURN gds.util.asNode(nodeId).wid, gds.util.asNode(nodeId).label"+lang+", gds.util.asNode(nodeId).description"+lang+", gds.util.asNode(nodeId).guid "
                            "ORDER BY pageRank DESC "
                            f"LIMIT {max_num}")
        for record in ppr_result:
            results.append(record)
        return results             


def get_ppr_subgraph(ppr_seed, max_num=10):
    '''
    Get a PPR based subgraph.
    
    :param ppr_seed: PPR seed node ID.
    :param max_num: maximum number of records to retrieve.
    :return: list type, list of the records output by Neo4j query
    '''  
    db_conn = db_connection.DB_Connection()
    with db_conn._driver.session() as session:
        tx = session.begin_transaction()
        ppr_result = tx.run(f"MATCH (p) WHERE ID(p) = {ppr_seed} "
                            "WITH p CALL gds.pageRank.stream('memex-graph', { maxIterations: 10, dampingFactor: 0.85, sourceNodes: [p] }) YIELD nodeId, score AS pageRank "
                            f"WITH gds.util.asNode(nodeId) AS n, pageRank   "
                            "MATCH (n)-[r]-(b) "
                            "WHERE EXISTS(b.wid) "
                            "RETURN * "
                            "ORDER BY pageRank DESC "
                            f"LIMIT {max_num}+10")
        
        ppr_result.graph()
        return ppr_result


def get_node_details(node_id, lang="en"):
    '''
    Get node main details.
    
    :param node_id: the ID of the source node to get its main details.
    :param lang: language to return
    :return: node main details
    '''
    if lang == "en":
        lang = ""
    else:  
        lang = "_" + lang   
        
    results = []
    db_conn = db_connection.DB_Connection()
    with db_conn._driver.session() as session:
        tx = session.begin_transaction()
        result = tx.run("MATCH (p) "
                        f"WHERE p.wid='{node_id}' "
                        "RETURN p.wid, p.label"+lang+", p.description"+lang+", p.guid, p.image, p.location.x, p.location.y")
        for record in result:
            results.append(record)

        if results:
            return results[0]
        else:
            return db_conn._error_status    


def get_node_neighbors(node_id, lang = "en"):
    '''
    Get the 1-hop neighbors of a node and their relation to the source node.
    
    :param node_id: the ID of the source node to get its neighbors.
    :param lang: language to return
    :return: list of relation type, neighbor id and neighbor label
    '''
    if lang == "en":
        lang_rel = ".en"  
        lang = ""
    else: 
        lang_rel = "." + lang 
        lang = "_" + lang  
        
    results = []
    db_conn = db_connection.DB_Connection()
    with db_conn._driver.session() as session:
        tx = session.begin_transaction()
        result = tx.run("MATCH (n)-[r]->(b) "
                        f"WHERE n.wid='{node_id}' "
                        "RETURN r"+lang_rel+", b.wid, b.label"+lang)
        for record in result:
            results.append(record)
        return results
    

def get_top_visually_similar_closest(image_emb, n, long, lat, meters, lang = "en"):
    '''
    Search for entites using image and location information. 
    
    :param image_emb: float array
    :param n: integer type, subset the top ranked results
    :param long: float type, longitude coordinates
    :param lat: float type, latitude coordinates
    :param meters: integer type, radial distance from point in meters
    :param lang: language to return
    :return: list of top n closest points by distance and similarity
    '''
    results = []
    db_conn = db_connection.DB_Connection()
    with db_conn._driver.session() as session:
        results = session.read_transaction(get_within_radius_visual, long=long, lat=lat,
                                        meters=meters, query=image_emb,lang=lang)

    return results[:n]


def get_top_visually_similar(image_emb, n, lang = "en"):
    '''
    Search for entites using image information. 
    
    :param image_emb: float array
    :param n: integer type, subset the top ranked results
    :param lang: language to return
    :return: list of top n closest points and visual similarity
    '''
    db_conn = db_connection.DB_Connection()
    with db_conn._driver.session() as session:
        results = session.read_transaction(get_visual, query=image_emb,lang=lang)

    return results[:n]
