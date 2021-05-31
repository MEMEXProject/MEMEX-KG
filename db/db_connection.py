"""
-----
Name: db_connection.py
Description:
Handles connection to Neo4j (selected Graph DB) connection and creation of nodes
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
# System Libraries
from neo4j import GraphDatabase
from neo4j import exceptions
# Project Components
import config as cfg


class DB_Connection(object):
    """
    DB_Connection handes connection to the Neo4j instance based on the config file connection details
    as well as handling inserion of nodes and edges.
    """
    def __init__(self):
        uri = cfg.neo4j["uri"]
        user = cfg.neo4j["username"]
        password = cfg.neo4j["password"]
        encrypted  =cfg.neo4j["encrypted"]

        self._driver = GraphDatabase.driver(uri, auth=(user, password),encrypted=encrypted)
        
        self._success_status = 0
        self._error_status = -1

    def close(self):
        self._driver.close()

    def initalise_neo4j(self):

        with self._driver.session() as session:
            session.run("CREATE CONSTRAINT ON (pla:Place) ASSERT pla.wid IS UNIQUE")
            session.run("CREATE CONSTRAINT ON (pla:Place) ASSERT exists(pla.wid)")
            session.run("CREATE CONSTRAINT ON (kno:Knowledge) ASSERT kno.wid IS UNIQUE")
            session.run("CREATE CONSTRAINT ON (kno:Knowledge) ASSERT exists(kno.wid)")
            session.run("CREATE CONSTRAINT ON (man:Manual) ASSERT man.mid IS UNIQUE")
            session.run("CREATE CONSTRAINT ON (man:Manual) ASSERT exists(man.mid)")


    def link_neighboring_places(self):
        """
        Created edges between nodes that are geographically close (until 150 meters).
        """
        with self._driver.session() as session:
            tx = session.begin_transaction()
            result = tx.run("MATCH (p1:Place), (p2:Place) "
                            "WHERE distance(p1.location, p2.location)<150 AND p1.id <> p2.id "
                            "CREATE (p1)-[r:NEIGHBORING"
                            "{distance:distance(p1.location, p2.location)}"
                            "]->(p2)"
                            "RETURN count(r);").single().value()
            tx.commit()
            print(result, " neighboring relationships created (<150m.)")

    def clear_everything(self):
        """
        Removes all the data..

        """        
        with self._driver.session() as session:
            tx = session.begin_transaction()
            tx.run("MATCH (n)"
                   "DETACH DELETE n;")
            tx.commit()
            print("Cleared everything")

    def build_list_rec(self, obj, res):
        """
        Extract all the items present in 'obj'. Handles cases in which list of lists are present.
        :param obj: 
        :param res: accumulator list to be returned
        :return: list containing all the retrieved items
        """
        if isinstance(obj, list):
            for e in obj:
                self.build_list_rec(e, res)
        elif isinstance(obj, str):
            obj = obj.replace('"', r'\"')
            res.append("\"" + obj + "\"")
        elif obj is not None:
            res.append("\"" + str(obj) + "\"")

    def queue_insert_node(self, data, additional_class=None,additional_languages=["fr","pt","es"]):
        """
        Inserts the node described by 'data' in the db.
        If the node has geographical coordinates, it is considered a ':Place' node, ':Knowledge' otherwise.
        
        :param data: a vector [properties, values] representing the node to be inserted.
        """
        with self._driver.session() as session:
            tx = session.begin_transaction()
            props = data[0]
            props_local = data[1]
            vals = data[2]
            node_type = "Place" if "coordinate_location" in props else "Knowledge"
            if not(additional_class is None):
                node_type = node_type + ":" + additional_class

            query = f"CREATE (a:{node_type} {{"
            for idx, (property_name, property_locals) in enumerate(zip(props,props_local)):
                if property_name == "location":
                  property_name = "location_other"
                if property_name == "coordinate_location":
                    if type(vals[idx][0]) is list:
                        res = []
                        for value in vals[idx]:
                            lat = value[0]
                            lon = value[1]
                            res.append(f"point({{latitude: {lat}, longitude: {lon} }})")
                        query += property_name + ": [" + ", ".join(res) + "],"
                    else:
                        lat = vals[idx][0]
                        lon = vals[idx][1]
                        query += f"location: point({{latitude: {lat}, longitude: {lon} }} ),"
                else:
                    res = []
                    self.build_list_rec(vals[idx], res)
                    if len(res) > 1:
                        query += property_name + ": [" + ", ".join(res) + "],"
                    elif len(res) == 1:
                        query += property_name + ": " + res[0] + ","
            query = query[:-1] + "})"  # remove trailing ","
            try:
                tx.run(query)
                tx.commit()
            except exceptions.ConstraintError:
                pass
            except exceptions.CypherSyntaxError:
                pass

    def link_father_son(self, father, prop, son, prop_local):
        """
        Creates an edge between nodes 'father' and 'son' with the name ':prop'.
        It handles the situation in which there is a list of pointed entities,
        in which case it simply removes 'son' from the list and creates the corresponding edge,
        thus it updates the father's list of pointed entities. 
        If 'father' or 'son' does not yet exist in the db, it creates nothing.
        
        :param father: wikidata entity id representing the father
        :param prop: name of the property
        :param son: wikidata entity id representing the son
        """
        assert isinstance(father, str) and isinstance(son, str) and \
            father[0] == 'Q' and father[1:].isdigit() and \
            son[0] == 'Q' and son[1:].isdigit()
        with self._driver.session() as session:
            statement_result = session.run(f"MATCH (father) WHERE father.wid=\"{father}\" RETURN father.{prop} as prop")
            father_properties = []
            for line in statement_result:
                if isinstance(line['prop'], list):
                    father_properties.extend(line['prop'])
                else:
                    father_properties.append(line['prop'])

            if son not in father_properties:
                print('Ignoring link')
                return  # the edge has already been added on previous calls
            # ABOVE ALWAYS OCCUR BECAUSE ONE DIRECTIONAL
            father_properties.remove(son)
            modify_property_query = f"MATCH (father) WHERE father.wid=\"{father}\" "
            if len(father_properties) > 0:
                modify_property_query += f"SET father.{prop} = "
                if len(father_properties) > 1:
                    modify_property_query += "[\"" + "\", \"".join(father_properties) + "\"]"
                else:
                    modify_property_query += f"\"{father_properties[0]}\""
            else:
                modify_property_query += f"REMOVE father.{prop}"

            # Prepare the multilingual 
            locals = ""
            for i, p in enumerate(prop_local):
              if i>0:
                locals += "," + p[0] + ":\"" + p[1] + "\""
              else:
                locals += p[0] + ":\"" + p[1] + "\""

            tx = session.begin_transaction()
            tx.run(f"MATCH (f), (s) "
                    f"WHERE f.wid=\"{father}\" and s.wid=\"{son}\" "
                    f"CREATE (f)-[r:{prop} {{ {locals} }} ]->(s)")
            
            tx.run(modify_property_query)
            tx.commit()

    def get_wikidata_ids_by_label(self, label):
        """
        Retrieves wikidata ids by label.
        :param label: Wikidata entity label
        :return: List of Wikidata entity id
        """  
        wids = []
        with self._driver.session() as session:
            tx = session.begin_transaction()
            result = tx.run("MATCH (p) "
                            "WHERE toLower(p.label) = $label "
                            "RETURN p.wid as wid", label=label)
            for record in result:
                wids.append(record["wid"])
        return wids

    def match_with_wikidata(self): 
        """
        Link entities which contain 'wids' property with wikidata entities.
        """  
        with self._driver.session() as session:
            tx = session.begin_transaction()
            tx.run("MATCH (a),(b) "
                   "WHERE EXISTS(a.wids) AND b.wid in a.wids "
                   "CREATE (a)-[r:mentions]->(b) ")
            tx.commit()

    def extract_wikidata_id(self, site_id):
        """
        Extract Wikidata id from site id.
        
        :param site_id: site id
        :return: Wikidata id
        """  
        return site_id.split("/")[-1]

    def already_present(self, wid):
        """
        Checks whether node 'wid' is already present in te db.
        :param wid: Wikidata entity id
        :return: Boolean value [True: wid is already present, False: otherwise]
        """
        with self._driver.session() as session:
            res = session.run(f"match (n) where n.wid=\"{wid}\" return count(n)>0 as bool")
            for r in res:
                return r['bool']

    def version(self):
        with self._driver.session() as session:
            res = session.run("call dbms.components() yield name, versions, edition unwind versions as version return name, version, edition;")
            for line in res:
                return line["edition"]
            
            
    ############################################################################################################
    #Story Creation
    ############################################################################################################ 

    def add_story(self, data):
        """
        Add a story node in the KG.
        
        :param data: a vector [properties, values] representing the story to be inserted.
        
        :return: sucess/failure code
        """
        with self._driver.session() as session:
            tx = session.begin_transaction()
            props = data[0]
            vals = data[1]
            
            query = "CREATE (a:Story {"
            for idx, property_name in enumerate(props):
                if property_name == "coordinate_location":
                    if type(vals[idx][0]) is list:
                        res = []
                        for value in vals[idx]:
                            lat = value[0]
                            lon = value[1]
                            res.append(f"point({{latitude: {lat}, longitude: {lon} }})")
                        query += property_name + ": [" + ", ".join(res) + "],"
                    else:
                        lat = vals[idx][0]
                        lon = vals[idx][1]
                        query += f"location: point({{latitude: {lat}, longitude: {lon} }} ),"
                else:
                    res = []
                    self.build_list_rec(vals[idx], res)
                    if len(res) > 1:
                        query += property_name + ": [" + ", ".join(res) + "],"
                    elif len(res) == 1:
                        query += property_name + ": " + res[0] + ","
            query = query[:-1] + "})"  # remove trailing ","
            try:
                tx.run(query)
                tx.commit()
            except:
                return self._error_status
        return self._success_status    
            
    def edit_story(self, story_id, data):
        """
        Edit a story node in the KG.
        
        :param story_id: story id.
        :param data: a vector [properties, values] representing the story to be edited.
        
        return: success/failure code
        """
        with self._driver.session() as session:
            tx = session.begin_transaction()
            props = data[0]
            vals = data[1]
            
            query = f"MATCH (p:Story{{story_id:{story_id}}}) SET "
            for idx, property_name in enumerate(props):
                if property_name == "coordinate_location":
                    if type(vals[idx][0]) is list:
                        res = []
                        for value in vals[idx]:
                            lat = value[0]
                            lon = value[1]
                            res.append(f"point({{latitude: {lat}, longitude: {lon} }})")
                        query += property_name + ": [" + ", ".join(res) + "],"
                    else:
                        lat = vals[idx][0]
                        lon = vals[idx][1]
                        query += f"p.location=point({{latitude: {lat}, longitude: {lon} }} ),"
                else:
                    res = []
                    self.build_list_rec(vals[idx], res)
                    if len(res) > 1:
                        query += "p." + property_name + "=[" + ", ".join(res) + "],"
                    elif len(res) == 1:
                        query += "p." + property_name + "=" + res[0] + ", "
            query = query[:-1] + ""  # remove trailing ","
            try:
                tx.run(query)
                tx.commit()
            except:
                return self._error_status
        return self._success_status  
            
    def delete_story(self, story_id):
        """
        Delete a story node from the KG.
        
        :param story_id: story id.
        
        return: success/failure code
        """
        with self._driver.session() as session:
            tx = session.begin_transaction()
          
            try:
                tx.run(f"MATCH (p:Story{{story_id:{story_id}}}) "
                       "DETACH DELETE p")
                tx.commit()
            except:
                return self._error_status
        return self._success_status  

    def connect_story_to_target_nodes(self, story_id, target_nodes, relation_type = "related_to"):
         """
         Connect a story node with a list of given nodes in the KG.
        
         :param story_id: story id.
         :param target_nodes: list of node ids of the target nodes.
         :param relation_type: relation to be added.
         """       
         with self._driver.session() as session:
            tx = session.begin_transaction()
            tx.run(f"MATCH (a:Story{{story_id:{story_id}}}), (b) "
                   f"WHERE  b.wid in {target_nodes} AND NOT (a)-[:{relation_type}]->(b) "
                   f"CREATE (a)-[:{relation_type}]->(b)")
            tx.commit()
            
    def connect_story_by_textual_sim(self, story_id, target_node_type, lang = "en", relation_type = "related_to", similarity_threshould = 0.7):
         """
         Connect a story node with other nodes in the KG by matching story label, description, and keywords with the labels of other nodes.
        
         :param story_id: story id.
         :param target_node_type: node type of the target node.
         :param lang: language to return
         :param relation_type: relation to be added.
         """
         if lang == "en":
             lang = ""
         else:  
             lang = "_" + lang
                
         with self._driver.session() as session:
            tx = session.begin_transaction()
            tx.run(f"MATCH (a:Story{{story_id:{story_id}}}) "
                   "UNWIND a.keywords+apoc.text.split(a.label, ' ')+apoc.text.split(a.description, ' ') as keyword "
                   f"MATCH (a:Story{{story_id:{story_id}}}), (b:{target_node_type}) "
                   f"WITH a, b, apoc.text.levenshteinSimilarity(keyword, b.label"+lang+") as similarity "
                   f"WHERE  similarity > {similarity_threshould} AND NOT (a)-[:{relation_type}]->(b) "
                   f"CREATE (a)-[:{relation_type}{{similarity:similarity}}]->(b)")
            tx.commit()

    def remove_story_connections(self, story_id, relation_type = "related_to"):
         """
         Remove the links between a story node and other  nodes in the KG.
        
         :param story_id: story id.
         :param relation_type: relation to be removed.
         """       
         with self._driver.session() as session:
            tx = session.begin_transaction()
            tx.run(f"MATCH (a:Story{{story_id:{story_id}}})-[r:{relation_type}]->(b) "
                   f"DELETE r")
            tx.commit()

    def link_stories_together(self, relation_type = "similar_to"):
         """
         Link story nodes together by matching story labels, descriptions and keywords. 
         And assign a similarity weight as link property.
        
         :param relation_type: relation to be added.
         """       
         with self._driver.session() as session:
            tx = session.begin_transaction()
            tx.run("MATCH (a:Story), (b:Story) "
                   f"WITH a, b, apoc.text.levenshteinSimilarity(apoc.text.join([a.label, a.description, apoc.text.join(a.keywords, ' ')],' '), apoc.text.join([b.label, b.description, apoc.text.join(b.keywords, ' ')],' ')) as similarity "
                   f"WHERE NOT (a)-[:{relation_type}]->(b) AND NOT a = b "
                   f"CREATE (a)-[:{relation_type}{{similarity:similarity}}]->(b)")
            tx.commit()
            
    ############################################################################################################
    #Story Viewing
    ############################################################################################################ 
    def get_stories_by_location(self, lat, long, meters, max_num=10):
        """
        Get a list of stories by location.
        
        :param lat: latitude.
        :param long: longitude.
        :param meters: radial distance in meters.
        :param max_num: maximum number of records to retrieve.
        
        :return: list type, list of the records output by Neo4j query
        """  
        results = []
        with self._driver.session() as session:
           tx = session.begin_transaction()
           result = tx.run("MATCH (p:Story) "
                           "WHERE distance(point({latitude:$lat, longitude:$long}),p.location) < $meters "
                           "RETURN p.story_id, p.label, p.description, p.image, p.audio, p.video, p.location.x, p.location.y, "
                           "distance(point({latitude:$lat, longitude:$long}),p.location) AS dist "
                           "ORDER BY dist ASC LIMIT $max_num", lat=lat, long=long, meters=meters, max_num=max_num)
   
           for record in result:
                results.append(record)
        return results  
           
    def get_story(self, story_id):
        """
        Get a story node from the KG.
        
        :param story_id: story id.
        
        return: sucess/failure code
        """
        results = []
        with self._driver.session() as session:
            tx = session.begin_transaction()
                     
            result = tx.run(f"MATCH (p:Story{{story_id:{story_id}}}) "
                            "RETURN p.label, p.description, p.image, p.audio, p.video, p.location.x, p.location.y")
            
            for record in result:
                results.append(record)
            
            if results:
                return results[0]
            else:
                return self._error_status
                       
    def get_story_connections(self, story_id, lang = "en", relation_type = "related_to"):
        """
        Get knowledge or place nodes related to a story.
        
        :param story_id: story id.
        
        :return: list type, list of the records output by Neo4j query
        """
        if lang == "en":
            lang = ""
        else:  
            lang = "_" + lang   
        
        results = []
      
        with self._driver.session() as session:
           tx = session.begin_transaction()
           result = tx.run(f"MATCH (a:Story{{story_id:{story_id}}})-[r:{relation_type}]->(p) "
                           "RETURN p.wid, p.label"+lang+", p.description"+lang+", p.image, p.location.x, p.location.y")
     
           for record in result:
               results.append(record)
        return results       
 
    def get_similar_stories(self, story_id, max_num = 10, relation_type = "similar_to"):
        """
        Get a list of similar stories related to a story.
        The result is sorted by similarity.
        
        :param story_id: story id.
        :param max_num: maximum number of records to retrieve.
        
        :return: list type, list of the records output by Neo4j query
        """
        results = []
      
        with self._driver.session() as session:
           tx = session.begin_transaction()
           result = tx.run(f"MATCH (a:Story{{story_id:{story_id}}})-[r:{relation_type}]->(p) "
                           "RETURN p.story_id, p.label, p.description, p.image, p.audio, p.video, p.location.x, p.location.y, r.similarity "
                           f"ORDER BY r.similarity DESC LIMIT {max_num}")

           for record in result:
               results.append(record)
        return results