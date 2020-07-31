"""
-----
Name: csv_reader.py
Description:
Handles bespoke ingestion from form output in the style of csv.
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
import csv
import argparse
# Project Components
import db.db_connection as db


def read_csv(filename):
	csv_file = open(filename, 'r')
	data = csv.reader(csv_file, delimiter=',')
	return data


def get_last_mid(session):
	data = session.run("MATCH (a:Manual) RETURN MAX(a.mid) as max")
	res = -1
	for line in data:
		if line['max'] is not None:
			res = line['max']
	return res


def csv_to_neo4j(db_conn, data):
	with db_conn._driver.session() as session:
		mid = get_last_mid(session)
		count = 0
		# mid = -1
		for i, line in enumerate(data):
			# line: title, description, author, category, category_2, category_3
			if i > 0:
				tx = session.begin_transaction()
				mid += 1
				query_node = "CREATE (a:Manual{"
				query_node += f"mid: {mid},"
				if len(line[1]) > 0:
					query_node += f"label: \"{line[1]}\","
				if len(line[2]) > 0:
					query_node += f"description: \"{line[2]}\","
				if len(line[3]) > 0:
					# here we can check for closest author (String matching)
					query_node += f"author: \"{line[3]}\","
				category_vector = ["\""+line[4]+"\""]  # required
				if len(line[5]) > 0:
					category_vector.append("\""+line[5]+"\"")
				if len(line[6]) > 0:
					category_vector.append("\""+line[6]+"\"")

				if len(category_vector) > 1:
					query_node += "category: ["+",".join(category_vector)+"]"
				else:
					query_node += f"category: \"{line[4]}\""
				query_node += "})"
				tx.run(query_node)
				count += 1

				query_edge = f"MATCH (a:Manual), (b:Knowledge) " \
							 f"WHERE a.mid={mid} and b.label=$label " \
							 f"CREATE (a)-[r:instance_of]->(b)"
				tx.run(query_edge, label=line[4])
				if len(line[5]) > 0:
					tx.run(query_edge, label=line[5])
				if len(line[6]) > 0:
					tx.run(query_edge, label=line[6])

				query_remove_property = f"MATCH (a:Manual) WHERE a.mid={mid} REMOVE a.category"
				tx.run(query_remove_property)

				tx.commit()
		print("Created", count, "nodes from csv file")

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Import from csv tool')
	parser.add_argument('-f', '--file', metavar='PATH', type=str, help='Path to the csv file')
	args = parser.parse_args()

	csv_filename = args.file
	db_conn = db.DB_Connection()
	data = read_csv(csv_filename)
	csv_to_neo4j(db_conn, data)
	db_conn.close()
