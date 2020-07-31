# MEMEX Project: Knowledge Graph
Abstract:
The MEMEX-KG creates a Geolocalised Cultural Heritage Knowledge Graph for exploitation within the MEMEX Project. Currently it provides tools for ingestion from 3rd Party Sources - Wikidata (https://www.wikidata.org/), Europeana(https://www.europeana.eu/), Mapillary (http://Mapillary.com) and a Custom Form  (powered by Wikidata categories and google Forms); to construct a graph rooted in the pilot areas. The MEMEX-KG focuses on tangible objects that can be localised and connects to intangible content collected and created across the project duration. 

Authors: \
Feliks Hibraj, Ca'Foscari University of Venice \
Sebastiano Vason, Ca'Foscari University of Venice \
Stuart James, Istituto Italiano di Tecnologia 


## Installation
1. Install the latest version of Neo4j (4.0+)
	- Download the latest version of Neo4j at https://neo4j.com/download/
	- Run the downloaded file, installation process follows
1. (Alternative) Set up a Neo4j sandbox:
	- Visit https://sandbox.neo4j.com/
	- Login
	- Click on "Start a new project", choose the "Blank Project" and confirm by pressing "Launch the project"
	- Now you have a neo4j sandbox project, which you can access with credentials found in "Connection details",
	in particular, use "Bolt URL" as the field "uri" in file credentials.txt, use "Username" and "Password" for the
	remaining 2 fields of file credentials.txt.
2. Create a conda environment containing the necessary libraries
```
conda env create --file kg_env.yml --name memex_kg
conda activate memex_kg
```

### [Optional] pymapillary Install
We adapt on the pymapillary (https://github.com/khmurakami/pymapillary) api therefore, to use the Mapillary ingestion you will need to install our version (in ingestion/pymapillary-memex/).
Follow these instructions to install:
```
cd ingestion/pymapillarymemex/
python setup.py install
```

## Config
Edit the file "config.py" adding the credentials and keys for the various services (please note you only need keys for the services you intend to ingest)
Example
```
neo4j = {
    "uri":"bolt://127.0.0.1:7687",
    "username": "user",
    "password":"pass",
    "encrypted": False
}


europeana = {
    "token":"key",
    "data_dir": "data/europeana/"
}

mapillary = {
    "api_key": "key",
    "per_page": 100,
    "data_dir": "data/mapillary/"
}
```

For Neo4j the config correspond to:
- uri: Neo4j Instance address
- username: Username for Neo4j
- password: Password for Neo4j
(See Neo4j docuemntation for setting up Neo4j)

Additional configuration details are inlined in the relevant sections below.

## Knowledge Graph Ingestion
For detailed usage help run:
```
python main.py -h 
```

In addition to clear the Neo4j Knowledge Graph run
```
python main.py  --mode 5
```
Below we outline example configuration settings and commands for the respective sources. 


### Wikidata
Example Command:
```
python main.py  --mode 0 --city barcelona --hops 2
```

### Europeana
Europeana Settings: [in config.py]:
- token: Requested from Europeana
- data_dir": Store of json files and images from Europeana

Example Command:
```
python main.py  --mode 2 --city barcelona
```


### Mapillary

Mapillary Settings: [in config.py]:
- api_key: Requested from Mapillary
- per_page: Caching setting (e.g. 100)
- data_dir: Store of json files and images from Mapillary

Example Command:
```
python main.py  --mode 3 --city barcelona
```

### Custom Form 
```
python main.py  --mode 4
```
The output can then be used [Custom Form](README_Custom_Form.md) using the google form service.

## Tested on 
 - Ubuntu 18.04 LTS
 - Sandbox Neo4j 3.5.11, Neo4j 4.1.0 (Desktop Version),  Neo4j 4.1.0 (community edition), 
 - Python 3.6.10

## Acknowledgments
The MEMEX project has received funding from the European Union's Horizon 2020 research and innovation programme under grant agreement No 870743.