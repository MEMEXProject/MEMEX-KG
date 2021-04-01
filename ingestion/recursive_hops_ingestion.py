"""
-----
Name: recursive_hops_ingestion.py
Description:
Wikidata look up neighbours to expand the Knowledge Graph.
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

import requests
import hashlib
import re
from tqdm import tqdm

prop_id = []  # list of wikidata property ids, e.g.: (P31, P625, ...) recorder so far
prop_lab = []  # list of corresponding 'en' labels, e.g.: ('instance_of', 'coordinate_location', ...)
prop_dirty = []  # dirty bit vector for the list of properties, {0: already on db, 1: not present on db}


def get_property_label(prop):
	"""
	Given a wikidata property id, it return a cleaned label retreived from wikidata.
	:param prop: Wikidata Property ID
	:return: Corresponding label (cleaned)
	"""
	for idx, v in enumerate(prop_id):
		if v == prop:
			return prop_lab[idx]
	url = f"https://www.wikidata.org/wiki/Special:EntityData/{prop}.json"
	r = requests.get(url=url)
	label = r.json()['entities'][prop]['labels']['en']['value']
	label = re.sub('[^a-zA-Z0-9 \n\.]', '', label)
	label = label.replace(" ", "_")
	label = label.replace("3", "three")
	prop_id.append(prop)
	prop_lab.append(label)
	prop_dirty.append(1)
	return label


def traverse_tree(claim_dict):
	"""
	Given a claim of the json object (relative to a node to be retrieved),
	this function extracts the value for that claim. In doing so, it first 
	detects the type of the claim ('globe-coordinate', 'time', ...), 
	and then proceeds with the extraction.
	:param claim_dict: Branch of the json object relative to a node
	:return: the value extracted from that claim
	"""
	mainsnak = claim_dict['mainsnak']
	dtype = mainsnak['datatype']
	if 'datavalue' in mainsnak.keys():
		if dtype == "wikibase-item":
			return mainsnak['datavalue']['value']['id']
		elif dtype == "globe-coordinate":
			lat = mainsnak['datavalue']['value']['latitude']
			lon = mainsnak['datavalue']['value']['longitude']
			return [lat, lon]
		elif dtype == "commonsMedia":
			fn = mainsnak['datavalue']['value'].replace(" ", "_")
			fn_enc = fn.encode('utf-8')
			m = hashlib.md5()
			m.update(fn_enc)
			checksum = m.hexdigest()
			a = checksum[0]
			b = checksum[1]
			return f"https://upload.wikimedia.org/wikipedia/commons/{a}/{a}{b}/{fn}"
			# alternative way:
			# query_image = f"""
			# PREFIX wd: <http://www.wikidata.org/entity/>
			# SELECT ?image
			# WHERE{{
			# 	wd:{entity_id} wdt:P18 ?image
			# }}"""
			# wikidata_site = pywikibot.Site("wikidata", "wikidata")
			# query_object = spq.SparqlQuery(repo=wikidata_site)
			# res = query_object.select(query_entity)  # returns a list, where data[0] is the first item,
			# return [res[0]['image']]
			# """
		elif dtype == "time":
			return mainsnak['datavalue']['value']['time']
	return None


def get_wikidata_value(claim):
	res = []
	for ref in claim:
		res.append(traverse_tree(ref))
	if len(res) == 1:
		return res[0]
	return res


def loop_on_properties(r, properties, values):
	"""
	It loops on all properties and call the corresponding function to extract
	a value from each claim.
	:param r: json file for the corresponding node to retrieve
	:param properties: at the end of the execution is going to contain the list of properties of the node
	:param values: at the end of the execution is going to contain the list of properties of the node
	"""
	r = r['claims']
	for key in r:
		value = get_wikidata_value(r[key])
		if value:
			properties.append(get_property_label(key))
			values.append(value)


# url = "http://www.wikidata.org/wiki/Special:EntityData/Q42"
def extract_all_info(url):
	"""
	Requests a wikidata entity and extracts all the claims (properties) for that node.
	
	:param url: url to the downloadeable wikidata entity 
	:return: [properties, values], properties: list of property labels retrieved, 
	values: list of property values retrieved
	"""
	entity_id = url.split("/")[-1]  # extract wikidata id, e.g.: 'Q42'
	r = requests.get(url=url)
	if (r.status_code == 200) and entity_id in r.json()['entities']:
		r = r.json()['entities'][entity_id]
		label = r['labels']['en']['value'] if 'en' in r['labels'].keys() else ""
		descriptions = r['descriptions']['en']['value'] if 'en' in r['descriptions'].keys() else ""
		properties = ['wid', 'label', 'description']
		values = [entity_id, label,descriptions]
		loop_on_properties(r, properties, values)
		return [properties, values]
	else:
		print("Bad Url["+str(r.status_code)+"]: ", url)
		return None


def get_wiki_entity_rec(wid, db_conn, n):
	"""
	Recursive function responsible for creating the node corresponding to 'wid', 
	recursively calling the function for all its sons and creating the corresponding edges with them.
	
	:param wid: Wikidata entity id to retrieve.
	:param db_conn: connection to the db
	:param n: number of hops (recursive calls on sons)

	"""
	if n > 0:
		if not db_conn.already_present(wid):
			url = f"http://www.wikidata.org/wiki/Special:EntityData/{wid}"
			data = extract_all_info(url)
			if data:
				db_conn.queue_insert_node(data)
				if n > 1:
					for idx, value in enumerate(data[1][1:]):
						if type(value) is list:
							for v in value:
								if isinstance(v, str) and len(v) > 1 and v[0] == 'Q' and v[1:].isdigit():
									get_wiki_entity_rec(wid=v, db_conn=db_conn, n=n-1)
									#print('Link: ',wid, '--',data[0][idx+1],'->',v)
									db_conn.link_father_son(father=wid, prop=data[0][idx+1], son=v)
						else:
							if isinstance(value, str) and len(value) > 1 and value[0] == 'Q' and value[1:].isdigit():
								get_wiki_entity_rec(wid=value, db_conn=db_conn, n=n-1)
								#print('Link: ',wid, '--',data[0][idx+1],'->',value)
								db_conn.link_father_son(father=wid, prop=data[0][idx+1], son=value)
			else:
				print("Not found: ", url)
		else:
			# print("Already present: ", wid)
			pass
	return


def download_n_hops_rec(starting_wids, db_conn, n):
	"""
	First it retrieves the list of mappings WPI(Wikidata Property ID, Corresponding Property Label),
	which is stored on the db for convenience, in order to avoid querying wikidata everytime.
	Then, for each wid (wikidata id), it calls get_wiki_entity_rec (recursive function responsible for
	retrieving wid node and all the sons recursively).
	Every 100 downloaded points, update the mapping list WPI.
	
	:param starting_wids: list of wikidata entity ids to retrieve 
	:param db_conn: connection to the db
	:param n: number of hops (recursive calls)
	"""
	# update the mapping of wikidata property ids to their labels (vectors prop_id, prop_lab)
	with db_conn._driver.session() as session:
		res = session.run("MATCH (n:WPI) return n.wpi as wpi, n.label as label")
		for line in res:
			prop_id.append(line['wpi'])
			prop_lab.append(line['label'])
			prop_dirty.append(0)
	# start processing all entities present in 'starting_wids'
	print("Processing ", len(starting_wids), " entities...")
	downloaded = 0
	for wid in tqdm(starting_wids):
		get_wiki_entity_rec(wid, db_conn, n)
		downloaded += 1
		# print("Downloaded: ", downloaded)
		if downloaded % 100 == 0:
			with db_conn._driver.session() as session:
				for idx, dirty in enumerate(prop_dirty):
					if dirty:
						#print('dirty add')
						session.run("CREATE (n:WPI{wpi: $wpi, label: $label})",
									wpi=prop_id[idx], label=prop_lab[idx])
						prop_dirty[idx] = 0
