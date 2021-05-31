"""
-----
Name: app.py
Description:
Handles connection to Neo4j (selected Graph DB) connection and creation of nodes
-----
Author: Hebatallah Mohamed {1}
Licence: 
Copyright: Copyright 2020, MEMEX Project
Credits: [Diego Pilutti {1}, Sebastiano Vascon {1}]
Affiliation: {1} Ca'Foscari University of Venice
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
import sys
sys.path.append('../')

from flask import Flask, request, make_response, jsonify
import jwt
import datetime
from functools import wraps
import db.db_connection as db
import db.db_search as db_search
import config as cfg
import networkx as nx
import numpy as np
import json
from algorithms.DominantSet import DominantSet_Clustering
from db.models import prepare_image,get_visual_model,get_visal_embedding
from PIL import Image
# initialize the flask app_final
app_final=Flask(__name__)
app_final.config['SECRET_KEY'] = 'thisisthesecretkey'

############################################################################################################
#Initalise
############################################################################################################ 

model_visual = None
def initalise(args):
    """
    Initialise any persistent components for the API
    :param args: arguments passed in
    :return: bool on success
    """    
    initalise_visual(args)
    return True


def initalise_visual(args):
    global model_visual
    model_visual = get_visual_model('ResNet18')
    print(model_visual)

############################################################################################################
#Authorization
############################################################################################################ 

@app_final.route('/login')
def login():
    """
    Allows users to login in order to obtain a security token required by all the endpoints of the API.
    
    :return: JSON response with the security token or an error message
    """    
    auth = request.authorization
    username = cfg.api["username"]
    password = cfg.api["password"]

    if auth and auth.username == username and auth.password == password:
        token = jwt.encode({'user' : auth.username, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)},
                           app_final.config['SECRET_KEY'])
        # token.decode('UTF-8')
        return jsonify({'token' : token })

    return make_response('Could not verify!', 401, {'WWW-Authenticate' : 'Basic realm="Login Required"'})

def token_required(f):  
    """
    Checks if the security token given by the login endpoint is passed as x-access-token in the header.
    
    :return: JSON response with an error message if the token is not present
    """ 
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message' : 'Token is missing!'}), 401
        return f(*args, **kwargs)
    return decorated

############################################################################################################
#Story Creation
############################################################################################################ 

@app_final.route('/add_story', methods=['POST'])
@token_required
def add_story():
    """
    Add story entity to the KG.
    
    :return: JSON response with the success status True/False
    """     
    req_data = request.get_json()
   
    properties = []
    values = []
    
    if 'story_id' in req_data:
        story_id = str(req_data["story_id"])
        properties.append('story_id')
        values.append(story_id)
    else:
        return jsonify({'message' : 'Missing story_id field.'}), 400   
        
    if 'label' in req_data:
        properties.append('label')
        values.append(req_data['label'])
    if 'description' in req_data:
        properties.append('description')
        values.append(req_data['description']) 
    if 'keywords' in req_data:
        properties.append('keywords')
        values.append(req_data['keywords'] + [' '])     
    if 'image' in req_data:
        properties.append('image')
        values.append(req_data['image']) 
    if 'audio' in req_data:
        properties.append('audio')
        values.append(req_data['audio']) 
    if 'video' in req_data:
        properties.append('video')
        values.append(req_data['video'])  
    if 'latitude' and 'longitude' in req_data:
        properties.append('coordinate_location')
        values.append([req_data['latitude'],req_data['longitude']])
        
    data = [properties, values]
    
    db_conn = db.DB_Connection()
    result = db_conn.add_story(data)
    
    if result == 0:
        
        if 'language' in req_data:
            lang = str(req_data["language"])
        else:
            lang = "en"
        
        db_conn.connect_story_by_textual_sim("'" + story_id + "'", "Knowledge", lang)
        db_conn.connect_story_by_textual_sim("'" + story_id + "'", "Place", lang)
        
        if 'connections' in req_data:
            connections = req_data['connections']
            db_conn.connect_story_to_target_nodes("'" + story_id + "'", connections)
                                      
        db_conn.link_stories_together()
        
        return jsonify(success=True)  
    else:
        return jsonify(success=False)


@app_final.route('/edit_story/<story_id>', methods=['PUT'])
@token_required
def edit_story(story_id):
    """
    Edit story entity in the KG.
    
    :return: JSON response with the success status True/False
    """       
    req_data = request.get_json()  
    
    properties = []
    values = []
    if 'label' in  req_data:
        properties.append('label')
        values.append(req_data['label'])
    if 'description' in req_data:
        properties.append('description')
        values.append(req_data['description'])
    if 'keywords' in req_data:
        properties.append('keywords')
        values.append(req_data['keywords'] + [' '])        
    if 'image' in req_data:
        properties.append('image')
        values.append(req_data['image']) 
    if 'audio' in req_data:
        properties.append('audio')
        values.append(req_data['audio']) 
    if 'video' in req_data:
        properties.append('video')
        values.append(req_data['video'])  
    if 'latitude' and 'longitude' in  req_data :
        properties.append('coordinate_location')
        values.append([req_data['latitude'],req_data['longitude']])            
 
    data = [properties, values]
    
    db_conn = db.DB_Connection()     
    result = db_conn.get_story(story_id) 
    if result == -1:
        return jsonify(success=False), 500
    else:    
        result = db_conn.edit_story(str(story_id), data)
        db_conn.remove_story_connections(str(story_id))
        
        if 'language' in req_data:
            lang = str(req_data["language"])
        else:
            lang = "en"
    
        db_conn.connect_story_by_textual_sim(str(story_id), "Knowledge", lang)
        db_conn.connect_story_by_textual_sim(str(story_id), "Place", lang)
        
        if 'connections' in req_data :
            connections = req_data['connections']
            db_conn.connect_story_to_target_nodes("'" + story_id + "'", connections)
            
        db_conn.link_stories_together()
        
        if result == 0:
            return jsonify(success=True)  
        else:
            return jsonify(success=False), 500


@app_final.route('/delete_story/<story_id>', methods=['DELETE'])
@token_required
def delete_story(story_id): 
    """
    Delete story entity from the KG.
    
    :return: JSON response with the success status True/False
    """   
    db_conn = db.DB_Connection() 
    result = db_conn.get_story(story_id) 
    if result == -1:
        return jsonify(success=False), 500
    else:    
        status = db_conn.delete_story(story_id)
        
        if status == 0:
            return jsonify(success=True)  
        else:
            return jsonify(success=False), 500

############################################################################################################
#Story Enrichment
############################################################################################################ 

@app_final.route('/search', methods=["GET"])
@token_required
def search():
    """
    Search for KG entities using free text and an optional location information (for dynamic clustering).
    
    :return: JSON response with the relevant KG entities
    """ 
    req_data = request.get_json()
    
    query = req_data['query']
    
    # static or dynamic
    if 'location_mode' in req_data:
        location_mode = str(req_data["location_mode"])
    else:
        location_mode = 'static' 
    
    # semantic (based on word embeddings) or fulltext     
    if 'text_mode' in req_data:
        text_mode = str(req_data["text_mode"])
    else:
        text_mode = 'fulltext'
     
    # Personalized PageRank (PPR) or Constrained Dominant Set (CDS)    
    if 'algorithm' in req_data:
        algorithm = str(req_data["algorithm"])
    else:
        algorithm = 'cds'
     
    # Language    
    if 'language' in req_data:
        lang = str(req_data["language"])
    else:
        lang = "en"    
     
    # Max num of records    
    if 'max_num' in req_data:
        max_num = int(req_data["max_num"])
    else:
        max_num = 10
    
    # Handle fulltext index        
    if text_mode == 'fulltext':    
        db_search.update_fulltext_index(lang)    
   
    # Get the seed node
    ppr_seed = ""
    if location_mode == "static": 
        top_similar = db_search.get_top_similar(text_mode, query, 1)
        if top_similar:
            ppr_seed = str(top_similar[0][3])
    else:
            
        if 'latitude' in req_data:
            latitude = int(req_data["latitude"])  
        else:
            return jsonify({'message' : 'Missing latitude field.'}), 400
       
        if 'longitude' in req_data:
            longitude = int(req_data["longitude"])  
        else:
            return jsonify({'message' : 'Missing longitude field.'}), 400
     
        if 'meters' in req_data:
            meters = int(req_data["meters"])  
        else:
            return jsonify({'message' : 'Missing meters field.'}), 400   
            
        top_similar = db_search.get_top_similar_closest(text_mode, query, 1, longitude, latitude, meters)
        if top_similar:
            ppr_seed = str(top_similar[0][4])
    
    results = []     
    if ppr_seed:
        db_search.update_named_graph()
        if algorithm == "ppr":
            results = db_search.get_top_ppr(ppr_seed, max_num, lang)
        else:
            # Subgraph extraction
            ppr_subgraph = db_search.get_ppr_subgraph(ppr_seed, max_num)                            
      
            G = nx.MultiDiGraph()
            nodeIds_dic = {}
            nodes = list(ppr_subgraph.graph()._nodes.values())
            for i, node in enumerate(nodes):
                G.add_node(node.id, labels=node._labels, properties=node._properties)
                nodeIds_dic[node.id] = i
            
            rels = list(ppr_subgraph.graph()._relationships.values())
            for rel in rels:
                G.add_edge(rel.start_node.id, rel.end_node.id, key=rel.id, type=rel.type, properties=rel._properties) 
                     
            ds_seed = nodeIds_dic[int(ppr_seed)]
    
            # DS Clustering
            dos = DominantSet_Clustering(G, epsilon=1.0e-4, cutoff=1.0e-5, binary=False)            
            dos.constrain_ds(G, [ds_seed])
            clusters, cohe, clusters_labels = dos.clustering()
      
            nodes = list(G.nodes(data=True))  
            for c in range(len(dos.clusters)):
                cluster_nodes = clusters[str(c)]['nodes']
                 # Put the seed node first
                if ds_seed in cluster_nodes:
                    cluster_nodes = np.delete(cluster_nodes, np.argwhere(cluster_nodes == ds_seed))
                    cluster_nodes = np.concatenate((np.array([ds_seed]), cluster_nodes), axis=0)
                for n in cluster_nodes:
                       temp = []
                       if('wid' in nodes[n][1]['properties']):
                           temp.append(nodes[n][1]['properties']['wid'])
                       else:
                           temp.append(None)
                           
                       if('label' in nodes[n][1]['properties']):
                           temp.append(nodes[n][1]['properties']['label'])  
                       else:
                           temp.append(None)
                           
                       if('description' in nodes[n][1]['properties']):
                           temp.append(nodes[n][1]['properties']['description'])  
                       else:
                           temp.append(None)                           
                           
                       if('guid' in nodes[n][1]['properties']):
                           temp.append(nodes[n][1]['properties']['guid']) 
                       else:
                           temp.append(None)
                           
                       results.append(temp)         
            results =  results[:max_num]   
    # prepare the response
    dict_res={}
    for i in range(len(results)):
        temp={}
        wid = results[i][0]
        temp['wid'] = wid
        temp['label'] = results[i][1]
        temp['description'] = results[i][2]
        temp['url'] = results[i][3] if results[i][3] else "https://www.wikidata.org/wiki/" + wid
        
        neighbors = db_search.get_node_neighbors(wid, lang)
        dict_neighbors_res={}
        for n in range(len(neighbors)):
            dict_neighbors={}
            dict_neighbors["relation_type"] = neighbors[n][0]
            dict_neighbors["neighbor_wid"] = neighbors[n][1]
            dict_neighbors["neighbor_label"] = neighbors[n][2]
            dict_neighbors_res[n] = dict_neighbors
            
        temp['additional_info'] = dict_neighbors_res
        dict_res[i]=temp
    return dict_res
   
@app_final.route('/get_node_details', methods=['GET'])
@token_required
def get_node_details():
    """
    Retrieves node main details based on a given node ID.
    
    :return: JSON response with the node details
    """ 
    req_data = request.get_json()
    
    if 'wid' in req_data:
        wid = str(req_data["wid"])
    else:
        return jsonify({'message' : 'Missing wid field.'}), 400 
    
    if 'language' in req_data:
        lang = str(req_data["language"])
    else:
        lang = "en"

    result = db_search.get_node_details(wid, lang)
    if result == -1:
        return jsonify(success=False), 500
    else:
        resp={}
        wid = result[0]
        resp['wid'] = wid
        resp['label'] = result[1]
        resp['description'] = result[2]
        resp['url'] = result[3] if result[3] else "https://www.wikidata.org/wiki/" + wid
        resp['image'] = result[4]   
        resp['latitude'] = result[5]   
        resp['longitude'] = result[6]
        
        neighbors = db_search.get_node_neighbors(wid, lang)
        dict_neighbors_res={}
        for n in range(len(neighbors)):
            dict_neighbors={}
            dict_neighbors["relation_type"] = neighbors[n][0]
            dict_neighbors["neighbor_wid"] = neighbors[n][1]
            dict_neighbors["neighbor_label"] = neighbors[n][2]
            dict_neighbors_res[n] = dict_neighbors
            
        resp['additional_info'] = dict_neighbors_res
        return resp
    
############################################################################################################
#Story Viewing
############################################################################################################ 

@app_final.route('/get_story/<story_id>', methods=['GET'])
@token_required
def get_story(story_id):
    """
    Retrieves story details based on a given story ID.
    
    :return: JSON response with the story details
    """ 
    db_conn = db.DB_Connection()
    result = db_conn.get_story(story_id)
    if result == -1:
        return jsonify(success=False), 500
    else:
        resp={}
        resp['label']= result[0]
        resp['description'] = result[1]
        resp['image'] = result[2]   
        resp['audio'] = result[3]   
        resp['video'] = result[4]  
        resp['latitude'] = result[5]   
        resp['longitude'] = result[6]
        return resp

@app_final.route('/get_story_connections', methods=['GET'])
@token_required
def get_story_connections(): 
    """
    Retrieves the KG entities connected to a given story. 
    
    :return: JSON response with the list of KG entities
    """ 
    
    req_data = request.get_json()
    
    if 'story_id' in req_data:
        story_id = str(req_data["story_id"])
        story_id = "'" + story_id + "'"
    else:
        return jsonify({'message' : 'Missing story_id field.'}), 400 
    
    if 'language' in req_data:
        lang = str(req_data["language"])
    else:
        lang = "en"

    db_conn = db.DB_Connection()
    result = db_conn.get_story(story_id) 
    if result == -1:
        return jsonify(success=False), 500
    else:    
        result = db_conn.get_story_connections(story_id, lang)
        resp={}
        for i in range(len(result)):
            temp={}
            temp['wid']= result[i][0]
            temp['label']= result[i][1]
            temp['description'] = result[i][2]
            temp['image'] = result[i][3]    
            temp['latitude'] = result[i][4]   
            temp['longitude'] = result[i][5]   
            resp[i]=temp
        return resp
 
@app_final.route('/get_similar_stories', methods=['GET'])
@token_required
def get_similar_stories():
    """
    Retrieves stories similar to a given story.
    
    :return: JSON response with the list of stories
    """ 
    req_data = request.get_json()
    
    if 'story_id' in req_data:
        story_id = str(req_data["story_id"])
        story_id = "'" + story_id + "'"
    else:
        return jsonify({'message' : 'Missing story_id field.'}), 400 
    
    db_conn = db.DB_Connection()
    result = db_conn.get_story(story_id) 
    if result == -1:
        return jsonify(success=False), 500
    else:    
        if 'max_num' in req_data:
            max_num = int(req_data["max_num"])
        else:
            max_num = 10
              
        result = db_conn.get_similar_stories(story_id, max_num)
        resp={}
        for i in range(len(result)):
            temp={}
            temp['story_id']= result[i][0]
            temp['label']= result[i][1]
            temp['description']= result[i][2]
            temp['image'] = result[i][3]
            temp['audio'] = result[i][4]    
            temp['video'] = result[i][5]  
            temp['latitude'] = result[i][6] 
            temp['longitude'] = result[i][7]
            temp['sim'] = result[i][8]
            resp[i]=temp
        return resp
    
@app_final.route('/get_stories_by_location', methods=["GET"])
@token_required
def get_stories_by_location():
    """
    Retrieves stories by a given location.
    
    :return: JSON response with the list of stories
    """  
    req_data = request.get_json()  
        
    if 'latitude' in req_data:
        latitude = int(req_data["latitude"])  
    else:
        return jsonify({'message' : 'Missing latitude field.'}), 400
   
    if 'longitude' in req_data:
        longitude = int(req_data["longitude"])  
    else:
        return jsonify({'message' : 'Missing longitude field.'}), 400
 
    if 'meters' in req_data:
        meters = int(req_data["meters"])  
    else:
        return jsonify({'message' : 'Missing meters field.'}), 400
        
    if 'max_num' in req_data:
        max_num = int(req_data["max_num"])
    else:
        max_num = 10     
 
    db_conn = db.DB_Connection()
    result = db_conn.get_stories_by_location(latitude, longitude, meters, max_num)

    res={}
    for i in range(len(result)):
        temp={}
        temp['story_id']= result[i][0]
        temp['label']= result[i][1]
        temp['description']= result[i][2]
        temp['image'] = result[i][3]
        temp['audio'] = result[i][4]    
        temp['video'] = result[i][5]  
        temp['latitude'] = result[i][6] 
        temp['longitude'] = result[i][7]
        temp['dist'] = result[i][8]
        res[i]=temp
    return res

@app_final.route('/search_image', methods=["POST"])
@token_required
def search_image():
    if type(model_visual) == type(None):
        print('Model missing')
        return jsonify(success=False), 500

    image = Image.open(request.files['image'].stream)
    image = prepare_image(image)
    emb = get_visal_embedding(model_visual, image)
    emb = [float(x) for x in emb]
    req_data = request.form.to_dict()
    print(req_data)
    if 'max_num' in request.form:
        max_num = int(req_data["max_num"])
    else:
        max_num = 10
    
    if 'meters' in req_data:
        meters = float(req_data["meters"])
    else:
        meters=1000
        
    if 'language' in req_data:
        lang = str(req_data["language"])
    else:
        lang = "en"

    if ('latitude' in req_data) and ('longitude' in req_data): 
        latitude = float(req_data["latitude"])
        longitude = float(req_data["longitude"])  
        results = db_search.get_top_visually_similar_closest(emb,max_num,longitude,latitude,meters,lang)

        dict_res={}
        for i in range(len(results)):
            print(results[i])
            temp={}
            temp['wid'] = results[i]["wid"]
            temp['label']=results[i]["label"]
            temp['image_url']=results[i]["image_url"]
            temp['description'] = results[i]["description"]
            temp['image_similarity'] = results[i]["similarity"]
            temp['location'] = results[i]["location"]
            temp['distance'] = results[i]["dist"]
            #temp['url'] = results[i][4] if results[i][4] else "https://www.wikidata.org/wiki/" + results[i][0]
            dict_res[i]=temp
        print(dict_res)
        return dict_res
    else:
        results = db_search.get_top_visually_similar(emb,max_num,lang)

        dict_res={}
        for i in range(len(results)):
            print(results[i])
            temp={}
            temp['wid'] = results[i]["wid"]
            temp['label']=results[i]["label"]
            temp['image_url']=results[i]["image_url"]
            temp['description'] = results[i]["description"]
            temp['image_similarity'] = results[i]["similarity"]
            if results[i]["location"]:
                temp['location'] = [results[i]["location"][0],results[i]["location"][1]]
            #temp['url'] = results[i][4] if results[i][4] else "https://www.wikidata.org/wiki/" + results[i][0]
            dict_res[i]=temp
        print(dict_res)
        return dict_res




if __name__=="__main__":
    """
    Main method to start the APIs on the defined host with SSL handling.
    
    """ 
    initalise(None)
    
    host = cfg.api["host"]
    port = cfg.api["port"]
    if cfg.api["encrypted"]:
      cert = cfg.api["cert"]
      key = cfg.api["key"]
      app_final.run(host=host, port=port, debug=True, ssl_context=(cert, key))
    else:
      app_final.run(host=host, port=port, debug=True)
