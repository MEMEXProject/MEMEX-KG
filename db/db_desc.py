"""
-----
Name: db_desc.py
Description:
Handles retrieving entity descriptions and embeddings.
-----
Author: Diego Pilutti {1}
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
from wikidata.client import Client
from db import db_connection
client = Client()
from db.models import avg_feature_vector
from tqdm import tqdm
import os
import wget

def get_wids(overwrite=True,with_image=False):
    '''
    Get the wids and labels of all the entites in the KG.
    
    :param overwrite: flag if true return entity wids regardless of having descriptions or not
    :param with_image: filters for only nodes that have images
    :return: list of entity wids and labels
    '''
    db_conn = db_connection.DB_Connection()
    with db_conn._driver.session() as session:
        if overwrite:
            if with_image:
                query = """
                MATCH (p) WHERE EXISTS (p.wid) AND EXISTS (p.image)
                RETURN p.wid, p.label, p.image
                """
            else:
                query = """
                MATCH (p) WHERE EXISTS (p.wid)
                RETURN p.wid, p.label
                """

        else:
            if with_image:
                query = """
                            MATCH (p) WHERE EXISTS (p.wid) AND EXISTS (p.image) AND (NOT EXISTS (p.description) OR NOT EXISTS (p.image_emb))
                            RETURN p.wid, p.label, p.image
                            """
            else:
                query = """
                            MATCH (p) WHERE EXISTS (p.wid) AND NOT EXISTS (p.description)
                            RETURN p.wid, p.label
                            """

        results = session.run(query)
        l=[]
        if with_image:
            for i in results:
                l.append( [i[0],i[1],i[2]] )
        else:
            for i in results:
                l.append( [i[0],i[1]] )
    db_conn.close()
    return l


def set_embedding_w2v(tx, wid, desc, emb, wikidesc=""):
    '''
    Insert word2vec generated embeddings as a new property in the entity.
    
    :param tx: transaction object for the neo4j driver
    :param wid: dict, wid reference for the entities
    :param emb: object containing the W2V embeddings of the descriptions
    :param wikidesc: wikipedia description
    :return: runs the SET query to update entities in the Neo4j db
    '''
    result = tx.run("MATCH (p)"
                    "WHERE p.wid= $wid "
                    "SET p.description_w2v = $emb "
                    "SET p.description = $desc "
                    "SET p.description_wikipedia = $wikidesc "
                    "RETURN p.wid,p.description,p.description_w2v,p.description_wikipedia ", wid=wid, desc=desc, emb=emb, wikidesc=wikidesc)

    return result

def set_embedding_visual(tx, wid, emb):
    '''
    Insert word2vec generated embeddings as a new property in the entity.
    
    :param tx: transaction object for the neo4j driver
    :param wid: dict, wid reference for the entities
    :param emb: object containing the W2V embeddings of the descriptions
    :param wikidesc: wikipedia description
    :return: runs the SET query to update entities in the Neo4j db
    '''
    result = tx.run("MATCH (p)"
                    "WHERE p.wid= $wid "
                    "SET p.image_emb = $emb "
                    "RETURN p.wid,p.image_emb ", wid=wid, emb=emb)

    return result

import wikipedia

def update_desc_emb(nodes,lang='en', wikipedia_sentences=2):
    '''
    Get node descriptions from Wikidata enriched with Wikipedia descriptions,
    generate embeddings based on the labels and descriptions,
    and set the embeddings as node property.
    
    :param nodes: dict, node ids and labels
    :param lang: language (default 'en')
    :param wikipedia_sentences: number of sentences to get from wikipedia (default 2)
    :return: a confirmation message
    '''
    db_conn = db_connection.DB_Connection()
    session = db_conn._driver.session()

    print(len(nodes))

    for wid,label in tqdm(nodes):

        wikipedia_descr = ""

        try:
            wikipedia_descr = wikipedia.summary(label, sentences=wikipedia_sentences)
        except:
            pass

        desc = ""
        try:
            entity = client.get(wid, load=True)
            if entity.description:
                descriptions = entity.description.texts
                if bool(descriptions):
                    if lang in descriptions.keys():
                        desc = descriptions[lang]
        except:
            pass

        text = label + "\n" + desc + "\n" + wikipedia_descr
        emb = avg_feature_vector(text)
        emb = [float(x) for x in emb]
        set_embedding_w2v(session, wid, desc, emb, wikipedia_descr)

    return "Desc and embeddings updated successfully"



def update_visual_desc_emb(nodes,model='ResNet18', temp_folder='data/images/', keep_images=False,throttle=2):
    '''
    Fetches the image creates a visual embedding using the described model
    
    :param nodes: array of arrays [[node ids, label, image url]]
    :temp_folder: the folder the images will be downloaded (temporarily if keep_images = false)
    :keep_images: whether to not delete the image
    :return: True on success
    '''
    from db.models import prepare_image_from_file,get_visual_model,get_visal_embedding
    import time
    os.makedirs(temp_folder, exist_ok=True)
    db_conn = db_connection.DB_Connection()
    session = db_conn._driver.session()
    model = get_visual_model(model)

    for wid,label,image_url in tqdm(nodes):
        # Encode only the first image (most common scenario)
        if type(image_url) == list:
            image_url = image_url[0]
        ext = image_url[-3:]
        filepath =  temp_folder + wid + '.' + ext
        filename = wget.download(image_url,filepath)
        I = prepare_image_from_file(filepath)
        if type(I) == type(None):
            continue
        emb = get_visal_embedding(model,I)
        emb = [float(x) for x in emb]
        set_embedding_visual(session, wid, emb)
        if not  keep_images:
            os.remove(filepath)
        time.sleep(throttle)

    return True