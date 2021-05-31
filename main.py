"""
-----
Name: main.py
Description:
Primary script to build the various aspects of the Knowledge Graph from selected 3rd party 
sources.
-----
Author: [Diego Pilutti {1}, Hebatallah Mohamed {1}]
Licence: 
Copyright: Copyright 2020, MEMEX Project
Credits: [Sebastiano Vascon {1}, Feliks Hibraj {1}, Stuart James {2}]
Affiliation: {1} Ca'Foscari University of Venice, {2} Istituto Italiano di Tecnologia 
License: BSD
Version: 1.0.0
Last Major Release Date: 31/03/2021
Maintainer: MEMEX Project
Email: contact@memexproject.eu
Status: Dev (Research)
Acknowledgment: 
This project has received funding from the European Union's Horizon 2020
research and innovation programme under grant agreement No 870743.
"""
# System Libraries
import argparse
# Project Components
import db.db_connection as db
import ingestion.wikidata_ingestion_places as wip
import ingestion.europeana_ingestion_places as eip
# import ingestion.mapillary_ingestion_places as mip
import ingestion.recursive_hops_ingestion as rhi
import ingestion.csv_reader as csv_reader
from ingestion.utils import str2bool
import db.extract_images as extract
import db.db_desc as db_desc
import db.db_search as db_search
import config as cfg
import tagme
from tqdm import tqdm

# Set the authorization token for subsequent calls.
tagme.GCUBE_TOKEN = cfg.europeana["tagme_token"]

def wikidata_ingest_pilots(hops, cities):
    """
    Reads the list of desired cities to ingest (Default: 'list_cities.txt')
    Retrieves the list of wikidata entity ids for each city, and calls
    download_n_hops_rec function in order to start recursive retrieval.
    
    :param hops: number of recursive hops
    :param cities: list of cities to retrieve
    """
    db_conn = db.DB_Connection()
    for city in cities:
        print("Wikidata ingestion...", city)
        data = wip.query_only_id_bboxes(city)
        starting_urls = []
        for line in data:
            # line is a wid of the format "wd:Q* ", we need only "Q* "
            starting_urls.append(line['place'].split("/")[-1])
        rhi.download_n_hops_rec(starting_urls, db_conn, hops,additional_languages=cfg.local["additional_country"])
    db_conn.close()


def europeana_ingest_pilots(cities, link_to_nodes=False, annotation_threshold=0.1):
    """
    Reads the list of desired cities to ingest (Default: 'list_cities.txt')
    Retrieves the list of europeana items and adds to Neo4j.
    
    :param cities: list of cities to retrieve
    :param link_to_nodes: a flag for linking the ingested entities to existing entities in the graph
    :param annotation_threshold: TagMe annotation threshold
    """
    db_conn = db.DB_Connection()
    wikidata_found = False
    for city in cities:
        print("Europeana ingestion...", city)
        data = eip.query_only_id_bboxes(city, db_conn=db_conn, link_to_nodes=link_to_nodes, annotation_threshold=annotation_threshold)

        # print("Processing ", len(data), " entities...")
        # for n in tqdm(data):
        #     if link_to_wikidata:
        #         #Add wikidata wids
        #         wiki_titles = []
        #         for idx, property_name in enumerate(n[0]):
        #             if property_name == "label" or property_name == "description" or property_name == "dcCreator":
        #                 value = n[1][idx]
        #                 europeana_annotations = tagme.annotate(value)
        #                 if europeana_annotations:
        #                     for ann in europeana_annotations.get_annotations(annotation_threshold):
        #                         t = ann.entity_title
        #                         t = t[0].lower() + t[1:]
        #                         wiki_titles.append(t)
        #
        #             if property_name == "dcCreator":
        #                 print(n[1][idx])
        #
        #         wiki_titles = list(dict.fromkeys(wiki_titles))
        #         all_wids = []
        #         for title in wiki_titles:
        #             wids = db_conn.get_wikidata_ids_by_label(title)
        #             if wids:
        #                 all_wids.extend(wids)
        #
        #         if all_wids:
        #             wikidata_found = True
        #             n[0].append("wids")
        #             n[1].append(all_wids)
        #
        #     #Insert the node
        #     db_conn.queue_insert_node(n)
        #
        # #Link to wikidata nodes
        # if link_to_wikidata and wikidata_found:
        #     db_conn.match_with_wikidata()
             
    db_conn.close()

# def mapillary_ingest_pilots(cities):
#     """
#     Reads the list of desired cities to ingest (Default: 'list_cities.txt')
#     Retrieves the list of mapillary image items and adds to Neo4j.
#
#     :param cities: list of cities to retrieve
#     """
#     db_conn = db.DB_Connection()
#     for city in cities:
#         print("Mapillary ingestion...", city)
#         data = mip.query_only_id_bboxes(city)
#         for n in data:
#             db_conn.queue_insert_node(n)
#     db_conn.close()

if __name__ == "__main__":
    """
    Data ingested from three sources
    """
    parser = argparse.ArgumentParser(description='MEMEX H2020 Knowledge Graph Ingestion Tool')
    parser.add_argument('--mode', metavar='N', default=0, type=int,
                        help="Modality ["
                             "0:Wikidata ingestion tool (--city or --cities), "
                             "1:Import nodes from a csv (-f, --file), "
                             "2:Europeana ingestion tool (--city or --cities), "
                             # "3:Mapillary ingestion tool (--city or --cities), "
                             "4:Category Vector (used for creating the form), "
                             "5:Clean Database,"
                             "6: Category Vectors,"
                             "7: Add Descriptions and Embeddings,"
                             "7: Search,"
                             "8: Drop fulltext index]")
    
    parser.add_argument('--hops', metavar='N', default=2, type=int,
                        help='[Mode 0] Number of hops (Default: 2)')
    parser.add_argument('--cities', metavar='PATH', type=str,
                        help='[Mode 0] Path to the file containing the list of cities to retrieve')
    parser.add_argument('--city', metavar='CITY', type=str,
                        help='[Mode 0] Run the wikidata/europeana ingestion tool on CITY')
    parser.add_argument('--link_to_nodes', metavar='link_to_nodes', type=str2bool,
                        help='[Mode 2] Link europeana with existing nodes in the MEMEX-KG')
    parser.add_argument('--img_store', metavar='imgpath', type=str,
                        help='[Mode 6] Location to store images')
    parser.add_argument('-f', '--file', metavar='PATH', type=str,
                        help='[Mode 1] Path to the csv file generated from the google form')
    parser.add_argument('--lang', default="en", metavar='language of the descriptions to be ingested', type=str,
                        help='[Mode 7] Language of the descriptions to be ingested from wikipedia')
    parser.add_argument('--overwrite_embedding', default=True, metavar='Overwrite existing embeddings', type=str2bool,
                        help='[Mode 7] Boolean for overwriting existing description and embeddings if any')
    parser.add_argument('--search_mode', metavar='search mode', type=str,
                        help='[Mode 8] Search mode: semantic or fulltext')
    parser.add_argument('--lat', metavar='lat', type=float,
                        help='[Mode 8] Latitude coordinates')
    parser.add_argument('--long', metavar='long', type=float,
                        help='[Mode 8] Longitude coordinates')
    parser.add_argument('--k', default=10, metavar='topK', type=int,
                        help='[Mode 8] Get the top K')
    parser.add_argument('--query', metavar='text query', type=str,
                        help='[Mode 8] Text query')
    parser.add_argument('--meters', default=5000, metavar='text query', type=int,
                        help='[Mode 8] Radial distance in meters')
    parser.add_argument('--verbose', type=str2bool, default=False)
    args = parser.parse_args()
    
    # Check if Community
    db_conn = db.DB_Connection()
    neo4j_version = db_conn.version()
    db_conn.close()
    if args.verbose:
        print("[INFO] Neo4j Currently running on", neo4j_version)

    #if 'community' not in neo4j_version:
        #print('not community')
        #db_conn = db.DB_Connection()
        #db_conn.initalise_neo4j()
        #db_conn.close()

    if args.mode == 0:  # Wikidata ingestion tool
        if args.cities:
            f = open(args.cities, 'r')
            cities = []
            for city in f:
                cities.append(city)
        elif args.city:
            cities = [args.city]
        else:
            print("Please specify a city (--city CITY) or the path to a list of cities (--cities PATH) to retrieve")
            cities = []
        wikidata_ingest_pilots(hops=args.hops, cities=cities)
    elif args.mode == 1:  # Import from csv
        if args.file:
            csv_filename = args.file
            db_conn = db.DB_Connection()
            data = csv_reader.read_csv(csv_filename)
            csv_reader.csv_to_neo4j(db_conn, data)
            db_conn.close()
        else:
            print("Please specify a filename for the csv with -f PATH, --file PATH")
    elif args.mode == 2:  # Import from Eurpoeana
        if args.cities:
            f = open(args.cities, 'r')
            cities = []
            for city in f:
                cities.append(city)
        elif args.city:
            cities = [args.city]
        else:
            print("Please specify a city (--city CITY) or the path to a list of cities (--cities PATH) to retrieve")
            cities = []
        europeana_ingest_pilots(cities=cities, link_to_nodes=args.link_to_nodes)
    # elif args.mode == 3:  # Import from Mapillary
    #     if args.cities:
    #         f = open(args.cities, 'r')
    #         cities = []
    #         for city in f:
    #             cities.append(city)
    #     elif args.city:
    #         cities = [args.city]
    #     else:
    #         print("Please specify a city (--city CITY) or the path to a list of cities (--cities PATH) to retrieve")
    #         cities = []
    #     mapillary_ingest_pilots(cities=cities)
    elif args.mode == 4:  # Category vector
        db_conn = db.DB_Connection()
        with db_conn._driver.session() as session:
            res = session.run(
                "MATCH ()-[r:instance_of]->(b) RETURN b.label as lab, count(b.label) as cnt ORDER BY lab ASC")
            result = []
            for item in res:
                result.append("\"" + item['lab'] + "\"")
            print("[" + ", ".join(result) + "]")
        db_conn.close()

    elif args.mode == 5:  # Clean database
        text = input("Are you sure that you want to completely delete everything from the database?"
              "\ny/[n]\n")
        if text == 'y':
            db_conn = db.DB_Connection()
            with db_conn._driver.session() as session:
                db_conn.clear_everything()
            db_conn.close()
        else:
            pass

    elif args.mode == 6:  # Category vector
        db_conn = db.DB_Connection()
        extract.parse_graph(db_conn,args.img_store)
        db_conn.close()

    elif args.mode == 7:# description and embeddings
        nodes = db_desc.get_wids(overwrite=args.overwrite_embedding, with_image=False)
        db_desc.update_desc_emb(nodes, lang=args.lang)
        nodes = db_desc.get_wids(overwrite=args.overwrite_embedding, with_image=True)
        db_desc.update_visual_desc_emb(nodes)
        
    elif args.mode == 8:  # Search Mode
        if args.query:
            if args.long and args.lat:
                lat = float(args.lat)
                long = float(args.long)
                desc = args.query
                n = args.k
                meters = args.meters
                results = db_search.get_top_similar_closest(args.search_mode, desc, n, long, lat, meters)
                dict_res = {}
                for i in range(len(results)):
                    temp = {}
                    temp['wid'] = results[i][1]
                    temp['id'] = results[i][4]
                    temp['node'] = results[i][0]
                    temp['dist'] = results[i][2]
                    temp['sim'] = results[i][3]
                    dict_res[i] = temp
                print(dict_res)

            else:
                desc = args.query
                n = args.k
                results = db_search.get_top_similar(args.search_mode, desc, n)
                dict_res = {}
                for i in range(len(results)):
                    temp = {}
                    temp['wid'] = results[i][1]
                    temp['id'] = results[i][3]
                    temp['node'] = results[i][0]
                    temp['sim'] = results[i][2]
                    dict_res[i] = temp
                print(dict_res)
        else:
            if not args.long or not args.lat:
                print("please specify correct parameters for search")
            else:
                lat = float(args.lat)
                long = float(args.long)
                n = args.k
                meters = args.meters
                results = db_search.get_top_closest(n, long, lat, meters)
                dict_res = {}
                for i in range(len(results)):
                    temp = {}
                    temp['wid'] = results[i][1]
                    temp['id'] = results[i][3]
                    temp['node'] = results[i][0]
                    temp['dist'] = results[i][2]
                    dict_res[i] = temp
                print(dict_res)
                
    elif args.mode == 9:
        print("Generating FullText Indices")
        db_search.update_fulltext_index()         