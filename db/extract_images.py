"""
-----
Name: extract_images.py
Description:
Using the Neo4j collection pull down all the images
-----
Author: Stuart James {2}
Licence: 
Copyright: Copyright 2020, MEMEX Project
Credits: [Sebastiano Vascon {1}, Feliks Hibraj {1}]
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
import wget

def query_all_urls(db_conn):
    '''
    Get image urls for all the places in the database.
    
    :param db_conn: database connection
    :return: list of image urls
    '''
    with db_conn._driver.session() as session:
        tx = session.begin_transaction()
        nodes = tx.run("MATCH(n:Place) RETURN n")
        urls = []

        for node in nodes:
            n = node['n']
            if "image" in n:
                imgs = n["image"] 
                if not isinstance(imgs, list):
                    # Make a list for simple code
                    imgs = [imgs]
                
                for i,img in enumerate(imgs):
                    urls.append( {'id':n['wid'] + '_' + str(i), 'url':img } )
        print('URLs:', str(len(urls))) 
        return urls


def download_image_url(id_url, output_folder):
    '''
    Download image.
    
    :param id_url: image url
    :param output_folder: output folder
    '''
    ext = id_url['url'][-3:]
    filename = wget.download(id_url['url'], output_folder + id_url['id'] + '.' + ext)


def parse_graph(db_conn, output_folder):
    '''
    A wrapper for download image.
    
    :param id_url: image url
    :param output_folder: output folder
    '''
    urls = query_all_urls(db_conn)
    for url in urls:
        
        try:
            download_image_url(url,output_folder)
        except:
            print('[Error] Unable to download:', url)


