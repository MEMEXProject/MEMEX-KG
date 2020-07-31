"""
-----
Name: main.py
Description:
Primary script to build the various aspects of the Knowledge Graph from selected 3rd party 
sources.
-----
Author: Feliks Hibraj {1}
Licence: 
Copyright: Copyright 2020, MEMEX Project
Credits: [Sebastiano Vason {1}, Stuart James {2}]
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
# System Libraries
import argparse
# Project Components
import db.db_connection as db
import ingestion.wikidata_ingestion_places as wip
import ingestion.europeana_ingestion_places as eip
import ingestion.mapillary_ingestion_places as mip
import ingestion.recursive_hops_ingestion as rhi
import ingestion.csv_reader
from ingestion.utils import str2bool



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
		rhi.download_n_hops_rec(starting_urls, db_conn, hops)
	db_conn.close()


def europeana_ingest_pilots(cities):
	"""
	Reads the list of desired cities to ingest (Default: 'list_cities.txt')
	Retrieves the list of europeana items and adds to Neo4j.
	
	:param cities: list of cities to retrieve
	"""
	db_conn = db.DB_Connection()
	for city in cities:
		print("Europeana ingestion...", city)
		data = eip.query_only_id_bboxes(city)
		for n in data:
			db_conn.queue_insert_node(n)
	db_conn.close()

def mapillary_ingest_pilots(cities):
	"""
	Reads the list of desired cities to ingest (Default: 'list_cities.txt')
	Retrieves the list of mapillary image items and adds to Neo4j.
	
	:param cities: list of cities to retrieve
	"""
	db_conn = db.DB_Connection()
	for city in cities:
		print("Mapillary ingestion...", city)
		data = mip.query_only_id_bboxes(city)
		for n in data:
			db_conn.queue_insert_node(n)
	db_conn.close()

if __name__ == "__main__":
	"""
	Data ingested from three sources Mapillary
	"""
	parser = argparse.ArgumentParser(description='MEMEX H2020 Knowledge Graph Ingestion Tool')
	parser.add_argument('--mode', metavar='N', default=0, type=int,
	                    help="Modality ["
	                         "0:Wikidata ingestion tool (--city or --cities), "
	                         "1:Import nodes from a csv (-f, --file), "
	                         "2:Europeana ingestion tool (--city or --cities), "
													 "3:Mapillary ingestion tool (--city or --cities), "
	                         "4:Category Vector (used for creating the form), "
	                         "5:Clean Database]")
	parser.add_argument('--hops', metavar='N', default=2, type=int,
	                    help='[Mode 0] Number of hops (Default: 2)')
	parser.add_argument('--cities', metavar='PATH', type=str,
	                    help='[Mode 0] Path to the file containing the list of cities to retrieve')
	parser.add_argument('--city', metavar='CITY', type=str,
	                    help='[Mode 0] Run the wikidata/europeana ingestion tool on CITY')
	parser.add_argument('-f', '--file', metavar='PATH', type=str,
	                    help='[Mode 1] Path to the csv file generated from the google form')
	parser.add_argument('--verbose', type=str2bool, default=False)
	args = parser.parse_args()
	
	# Check if Community
	db_conn = db.DB_Connection()
	neo4j_version = db_conn.version()
	db_conn.close()
	if args.verbose:
		print("[INFO] Neo4j Currently running on", neo4j_version)

	if 'community' not in neo4j_version:
		db_conn = db.DB_Connection()
		db_conn.initalise_neo4j()
		db_conn.close()

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
		europeana_ingest_pilots(cities=cities)
	elif args.mode == 3:  # Import from Mapillary
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
		mapillary_ingest_pilots(cities=cities)
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
