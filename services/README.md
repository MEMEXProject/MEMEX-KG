# MEMEX_KG_API

The API objective is to enable the interaction between MEMEX application and MEMEX-KG. It provides functionalities to add, update or delete user stories in the KG. It also allow to search for entities in the KG, in order to enrich stories during the creation process. Furthermore, it provides functionalities for viewing stories, KG entites related to a story, and list similar stories. 


## Running the Application
Run the "app.py".
```
python app.py
```

## Endpoints

Below is the list of MEMEX API endpoints with examples of JSON requests to call the API:

1) "api host:port"/login 

    The login endpoint should be called before calling any of the other endpoints in order to authenticate the user.
    The request should include Basic Autherization username and passowrd properies with the values configured in the "config.py". 
    The response will include an x-access-token.
    All the subsequent endpoints require x-access-token in the header with the token recieved from the login. 


2) "api host:port"/add_story 

    Add a “Story” node in the KG, and link it with other KG entities if “connections” attribute is given.

    Additionally, the story will be linked automatically with the other nodes in the KG of type “Knowledge”, “Place” and “Story” using string matching. Story label, description and keywords will be used to match the created story with the other nodes in the KG. 

    If there is a matching found between a “Story” and a “Knowledge” or “Place” node, a “related_to” relation will be added. While similar stories will have a “similar_to” relation between them. 
    
    Example:

    ```
    { 
       “story_id”: <story ID> - type: string, (mandatory)  
       “label”: <story title> - type: string, (optional)  
       “description”: <story description> - type: string, (optional)  
       “keywords”: <story keywords> - type: string array, (optional)  
       “image”: <image URLs> - type: string array, (optional)  
       “audio”: <audio URLs> - type: string array, (optional)  
       “video”: <video URLs> - type: string array, (optional)  
       “latitude”: <latitude information> - type: digit, (optional)  
       “longitude”: <longitude information> - type: digit, (optional)  
       “language”: <language setting> - type: string, (optional, default = “en”)  
       “connections”: <wids of KG entities to be linked to the story> - type: string array (optional)
    } 
    ```

3) "api host:port"/edit_story/:story_id 

    Edit a 'Story' node in the KG. The linking with with other nodes in the KG will be updated. 

    Example:

    ```
    { 
       “label”: <story title> - type: string, (optional)  
       “description”: <story description> - type: string, (optional)  
       “keywords”: <story keywords - type: string array, (optional)  
       “image: <image URLs> - type: string array, (optional)  
       “audio: <audio URLs> - type: string array, (optional)  
       “video: <video URLs> - type: string array, (optional)  
       “latitude”: <latitude information> - type: digit, (optional)  
       “longitude”: <longitude information> - type: digit, (optional)  
       “language”: <language setting> - type: string, (optional, default = “en”)  
       “connections”: <wids of KG entities to be linked to the story> - type: string array (optional)
    } 
    ```

4) "api host:port"/delete_story/:story_id 

    Delete a 'Story' node from the KG. 
    

5) "api host:port"/search

    Retrieve a list of nodes of type 'Place' or 'Knowledge' based on textual query and with the help of KG clustering. 

    Example:

    ```
    { 
       “location_mode”: “static” or “dynamic” - type: string, (optional, default = “static”) 
       “text_mode”: “fulltext” or “semantic” - type: string, (optional, default = “fulltext”) 
       “algorithm”: “cds” or “ppr” - type: string, (optional, default = “cds”) 
       “query”: <free text> - type: string,  
       “latitude”: <latitude information> - type: digit, (optional)  
       “longitude”: <longitude information> - type: digit, (optional)  
       “meters”: <radial distance in meters> - type: digit, (optional) 
       “language”: <language setting> - type: string, (optional, default = “en”)  
       “max_num”: <max number of nodes to retrieve> - type: digit (optional, default=10)
    } 
    ```
    
6) "api host:port"/get_node_details

    Get node main details from the KG using a given node ID (wid attribute). 

    Example:

    ```
    { 
       “wid”: <Wikidata or Europeana unique ID> - type: string, (mandatory) 
       “language”: <language setting> - type: string, (optional, default = “en”)  
    } 
    ```  
    
7) "api host:port"/search_visual

    Retrieve a list of nodes of type “Place” or “Knowledge” based on visual query or additionally the location. 

    Example:

    ```
    { 
       “image”: “static” or “dynamic” - type: file, (mandatory)
       “latitude”: <latitude information> - type: digit, (optional)
       “longitude”: <longitude information> - type: digit, (optional)
       “meters”: <radial distance in meters> - type: digit, (optional)
       “language”: <language setting> - type: string, (optional, default = “en”)
       “max_num”: <max number of nodes to retrieve> - type: digit (optional, default=10)    
    } 
    ```  
    

8) "api host:port"/get_story/:story_id 

    Get a 'Story' node information from the KG. 
    

9) "api host:port"/get_story_connections

    Retrieve a list of nodes of type 'Place' or 'Knowledge' linked to a story (linked during the story creation). 

    Example:

    ```
    { 
       “story_id”: <story ID> - type: string, (mandatory)
       “language”: <language setting> - type: string, (optional, default = “en”)  
    } 
    ```      

10) "api host:port"/get_similar_stories

    Retrieve a list of similar stories (nodes of type 'Story') linked to a provided story (linked during the story creation). 

    Example:

    ```
    { 
       “story_id”: story id - type: text,  
       “max_num”: max number of nodes to retrieve - type: digit (optional, default=10) 
    } 
    ```

11) "api host:port"/get_stories_by_location 

    Retrieve a list of  stories (nodes of type 'Story') based on provided user location. 

    Example:

    ```
    { 
       “latitude”: latitude information - type: digit, (mandatory) 
       “longitude”: longitude information - type: digit, (mandatory) 
       “meters”: radial distance in meters - type: digit, (mandatory) 
       “max_num”: max number of nodes to retrieve - type: digit (optional, default=10) 
    } 
    ```


## Acknowledgments
The MEMEX project has received funding from the European Union's Horizon 2020 research and innovation programme under grant agreement No 870743.
