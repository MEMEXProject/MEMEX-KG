"""
-----
Name: config.py
Description:
Global settings and api keys for handling connections and APIs
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

neo4j = {
    "uri":"bolt://127.0.0.1:7687",
    "username": "neo4j",
    "password":"chicken",
    "encrypted": False
}


europeana = {
    "token":"L5irQjj8Y",
    "data_dir": "data/europeana/"
}

mapillary = {
    "api_key": "bC1vcjhnbjZraTVBemtVMWFBbVNwQTo2ZDUzMmNiNzA3NDEyNThm",
    "per_page": 100,
    "data_dir": "data/mapillary/"
}