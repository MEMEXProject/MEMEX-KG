"""
-----
Name: db_connection.py
Description:
Handles connection to Neo4j (selected Graph DB) connection and creation of nodes
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

    def queue_insert_node(self, data, additional_class=None):
        """
        Inserts the node described by 'data' in the db.
        If the node has geographical coordinates, it is considered a ':Place' node, ':Knowledge' otherwise.
        
        :param data: a vector [properties, values] representing the node to be inserted.
        """
        with self._driver.session() as session:
            tx = session.begin_transaction()
            props = data[0]
            vals = data[1]
            node_type = "Place" if "coordinate_location" in props else "Knowledge"
            if not(additional_class is None):
                node_type = node_type + ":" + additional_class

            query = f"CREATE (a:{node_type} {{"
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
            except exceptions.ConstraintError:
                pass
            except exceptions.CypherSyntaxError:
                pass

    def link_father_son(self, father, prop, son):
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
            tx = session.begin_transaction()
            tx.run(f"MATCH (f), (s) "
                    f"WHERE f.wid=\"{father}\" and s.wid=\"{son}\" "
                    f"CREATE (f)-[r:{prop}]->(s)")
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