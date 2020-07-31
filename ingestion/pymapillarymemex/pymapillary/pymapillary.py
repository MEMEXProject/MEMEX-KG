#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .error_handling import *

import requests
import wget

class Mapillary():

    def __init__(self, client_id):

        if client_id is None:
            raise Exception("No Client id inserted")

        self.root_url = "https://a.mapillary.com/v3"
        self.client_id = client_id

    # https://www.mapillary.com/developer/api-documentation/#pagination
    def get_pagnation_resources(self,link):

        """Get pagnation Resources

        Args:
            page_num (int): Number of pages to display. Default is 1.
            per_page (int): Number of responses per page. Default is 200.

        Return:
            raw_json (dict): Dictionary of the result json requested

        Raises:
            Exception error: Uses HTTP error handler to check status code

        """


        r = requests.get(link)
        http_error_handler(r.status_code)
        raw_json = r.json()
        next = None
        if 'next' in r.links:
            next = r.links['next']['url']
        return raw_json, next

    #https://www.mapillary.com/developer/api-documentation/#search-images
    def search_images(self, bbox=None, closeto=None, end_time=None,
                      image_keys=None, lookat=None, pano="false", per_page=200,
                      project_keys=None, radius=100, sequence_keys=None,
                      start_time=None, userkeys=None, usernames=None):

        """Search images by parameter

        Args:
            bbox (string): 	  Filter by the bounding box, given
                              as minx,miny,maxx,maxy. One string comma seperated.
            closeto (string): Filter by a location that images are close to,
                              given as longitude,latitude. One string comma
                              seperated.
            end_time (string): Filter images that are captured before end_time.
                               Must be a valid ISO 8601 date.
            image_keys (string): Filter images by a list of image keys. One
                                 string comma seperated.
            lookat (string): Filter images that images are taken in the
                             direction of the specified location using latitude
                             and longitude. One string comma seperated.
            pano (string):   Filter true for panoramic images or false for flat
                             images. true and false must be in a string
                             lower case.
            per_page (int): Number of responses per page. Default is 200.
            project_keys (string): 	Filter images by projects, given as
                                    project keys. One string comma seperated.
            radius (int):    Filter images within the radius parameter around
                             the closeto parameter location. Default 100 meters.
            sequence_keys: Filter images by sequences keys. One string comma
                           seperated.
            start_time:    Filter images that are captured since start_time.
                           Must be a valid ISO 8601 date.
            userkeys:      Filter images captured by users, given as user keys.
                           One string comma seperated.
            usernames:     Filter images captured by users, given as usernames.
                           One string comma seperated.

        Return:
            raw_json (dict): Dictionary of the result json requested

        Raises:
            Exception error: Uses HTTP error handler to check status code

        """

        url = self.root_url + "/images"

        data = {
                 'bbox': bbox,
                 'closeto': closeto,
                 'end_time': end_time,
                 'image_keys': image_keys,
                 'pano': pano,
                 'per_page': per_page,
                 'radius': radius,
                 'sequence_keys': sequence_keys,
                 'start_time': start_time,
                 'userkeys': userkeys,
                 'usernames': usernames,
                 'client_id': '{}'.format(self.client_id)
                }

        r = requests.get(url, params=data)
        http_error_handler(r)
        raw_json = r.json()
        next = None
        if 'next' in r.links:
            next = r.links['next']['url']
        return raw_json, next

    def get_image_feature_by_key(self, key):

        """Get a image feature by the image key

        Args:
            key (string):    Takes in a image key.

        Return:
            raw_json (dict): Dictionary of the result json requested

        Raises:
            Exception error: Uses HTTP error handler to check status code

        """

        url = self.root_url + "/images/" + key

        data = {
                 'client_id': '{}'.format(self.client_id)
                }

        r = requests.get(url, params=data)
        http_error_handler(r.status_code)
        raw_json = r.json()
        return raw_json

    def search_image_detections(self, bbox=None, closeto=None, image_keys=None,
                                layers=None, max_score=None, min_score=None,
                                per_page=200, radius=50, userkeys=None,
                                usernames=None, values=None):

        """Search image detections by parameters

        Args:
            bbox (string): 	  Filter by the bounding box, given
                              as minx,miny,maxx,maxy. One string comma seperated.
            closeto (string): Filter by a location that images are close to,
                              given as longitude,latitude. One string comma
                              seperated.
            image_keys (string): Filter images by a list of image keys. One
                                 string comma seperated.
            layers (string):  Filter image detections by layers.
            max_score (int):  Filter image detections with the maximum score.
            min_score (int):  Filter Image detections with the minimal score.
            per_page (int):   Number of responses per page. Default is 200.
            project_keys (string): 	Filter images by projects, given as
                                    project keys. One string comma seperated.
            radius (int):     Filter images within the radius parameter around
                              the closeto parameter location. Default 50 meters.
            userkeys:         Filter images captured by users, given as user
                              keys. One string comma seperated.
            usernames:        Filter images captured by users, given as
                              usernames. One string comma seperated.
            values:           Filter image detections by values.

        Return:
            raw_json (dict):  Dictionary of the result json requested

        Raises:
            Exception error:  Uses HTTP error handler to check status code

        """

        url = self.root_url + "/image_detections"

        data = {
                 'bbox': bbox,
                 'closeto': closeto,
                 'image_keys': image_keys,
                 'layers': layers,
                 'max_score': max_score,
                 'min_score': min_score,
                 'per_page': per_page,
                 'radius': radius,
                 'userkeys': userkeys,
                 'usernames': usernames,
                 'values': values,
                 'client_id': '{}'.format(self.client_id)
                }

        r = requests.get(url, params=data)
        http_error_handler(r.status_code)
        raw_json = r.json()
        next = None
        if 'next' in r.links:
            next = r.links['next']['url']
        return raw_json, next

    def search_sequences(self, bbox=None, end_time=None, per_page=200,
                         starred="false", start_time=None, userkeys=None,
                         usernames=None):

        """Search sequences

        Args:
            bbox (string): 	  Filter by the bounding box, given
                              as minx,miny,maxx,maxy. One string comma seperated.
            end_time (string): Filter images that are captured before end_time.
                              Must be a valid ISO 8601 date.
            per_page (int):   Number of responses per page. Default is 200.
            starred (string): Filter sequences that are starred (true) or
                              non-starred (false). Must be a string lowercase.
            start_time:       Filter images that are captured since start_time.
                              Must be a valid ISO 8601 date.
            userkeys:         Filter images captured by users, given as user
                              keys. One string comma seperated.
            usernames:        Filter images captured by users, given as
                              usernames. One string comma seperated.

        Return:
            raw_json (dict): dictionary of the result json requested

        Raises:
            Exception error: Uses HTTP error handler to check status code

        """

        url = self.root_url + "/sequences"

        data = {
                 'bbox': bbox,
                 'end_time': end_time,
                 'per_page': per_page,
                 'starred': starred,
                 'start_time': start_time,
                 'userkeys': userkeys,
                 'usernames': usernames,
                 'client_id': '{}'.format(self.client_id)
                }

        r = requests.get(url, params=data)
        http_error_handler(r.status_code)
        raw_json = r.json()
        next = None
        if 'next' in r.links:
            next = r.links['next']['url']
        return raw_json,next

    def get_sequence_by_key(self, key):

        """Get a sequence by key

        Args:
            key (string):    Takes in a sequence key.

        Return:
            raw_json (dict): Dictionary of the result json requested

        Raises:
            Exception error: Uses HTTP error handler to check status code

        """

        url = self.root_url + "/sequences/" + key

        data = {
                 'client_id': '{}'.format(self.client_id)
                }

        r = requests.get(url, params=data)
        http_error_handler(r.status_code)
        raw_json = r.json()
        return raw_json

    def search_changesets(self, bbox=None, per_page=200, states=None,
                          types=None, userkeys=None):

        """Search changesets

        Args:
            bbox (string): 	  Filter by the bounding box, given
                              as minx,miny,maxx,maxy. One string comma seperated.
            per_page (int):   Number of responses per page. Default is 200.
            states (string):  Filter by changeset states.
            types (string):   Filter by changeset types.
            userkeys:         Filter images captured by users,
                              given as user keys. One string comma seperated.

        Return:
            raw_json (dict):  Dictionary of the result json requested

        Raises:
            Exception error:  Uses HTTP error handler to check status code

        """

        url = self.root_url + "/changesets"

        data = {
                 'bbox': bbox,
                 'per_page': per_page,
                 'states': states,
                 'types': types,
                 'userkeys': userkeys,
                 'client_id': '{}'.format(self.client_id)
                }

        r = requests.get(url, params=data)
        http_error_handler(r.status_code)
        raw_json = r.json()
        next = None
        if 'next' in r.links:
            next = r.links['next']['url']
        return raw_json, next

    def get_changeset_by_key(self, key):

        """Get a changeset by key

        Args:
            key (string):    Takes in a changeset key.

        Return:
            raw_json (dict): Dictionary of the result json requested

        Raises:
            Exception error: Uses HTTP error handler to check status code

        """

        url = self.root_url + "/changesets/" + key

        data = {
                 'client_id': '{}'.format(self.client_id)
                }

        r = requests.get(url, params=data)
        http_error_handler(r.status_code)
        raw_json = r.json()
        return raw_json 

    def search_map_features(self, bbox=None, closeto=None, layers=None,
                            max_nbr_image_detections=None,
                            min_nbr_image_detections=None, per_page=200,
                            radius=100, userkeys=None, usernames=None,
                            values=None):

        """Search map features

        Args:
            bbox (string): 	  Filter by the bounding box, given
                              as minx,miny,maxx,maxy. One string comma seperated.
            closeto (string): Filter by a location that images are close to,
                              given as longitude,latitude. One string comma
                              seperated.
            layers (string):  Filter image detections by layers.
            max_nbr_image_detections (int):  The maximum number of image
                                             detections that detect the map
                                             feature.
            min_nbr_image_detections (int):  The minimum number of image
                                             detections that detect the map
                                             feature.
            per_page (int):   Number of responses per page. Default is 200.
            radius (int):     Filter images within the radius parameter around
                              the closeto parameter location. Default 50 meters.
            userkeys:         Filter images captured by users, given as user
                              keys. One string comma seperated.
            usernames:        Filter images captured by users, given as
                              usernames. One string comma seperated.
            values:           Filter image detections by values.

        Return:
            raw_json (dict):  Dictionary of the result json requested

        Raises:
            Exception error:  Uses HTTP error handler to check status code

        """

        url = self.root_url + "/map_features"

        data = {
                 'bbox': bbox,
                 'closeto': closeto,
                 'layers': layers,
                 'max_nbr_image_detections': max_nbr_image_detections,
                 'min_nbr_image_detections': min_nbr_image_detections,
                 'per_page': per_page,
                 'radius': radius,
                 'userkeys': userkeys,
                 'usernames': usernames,
                 'values': values,
                 'client_id': '{}'.format(self.client_id)
                }

        r = requests.get(url, params=data)
        http_error_handler(r.status_code)
        next = None
        if 'next' in r.links:
            next = r.links['next']['url']
        return raw_json, next

    def search_users(self, bbox=None, per_page=200, userkeys=None,
                     usernames=None):

        """Search users

        Args:
            bbox (string): 	  Filter by the bounding box, given
                              as minx,miny,maxx,maxy. One string comma seperated.
            per_page (int):   Number of responses per page. Default is 200.
            userkeys:         Filter images captured by users, given as user
                              keys. One string comma seperated.
            usernames:        Filter images captured by users, given as
                              usernames. One string comma seperated.

        Return:
            raw_json (dict): dictionary of the result json requested

        Raises:
            Exception error: Uses HTTP error handler to check status code
        """

        url = self.root_url + "/users"

        data = {
                 'bbox': bbox,
                 'per_page': per_page,
                 'userkeys': userkeys,
                 'usernames': usernames,
                 'client_id': '{}'.format(self.client_id)
                }

        r = requests.get(url, params=data)
        http_error_handler(r.status_code)
        raw_json = r.json()
        next = None
        if 'next' in r.links:
            next = r.links['next']['url']
        return raw_json, next

    def get_user_by_key(self, key):

        """Get a user by a userkey

        Args:
            key (string):    Takes in a user key.

        Return:
            raw_json (dict): Dictionary of the result json requested

        Raises:
            Exception error: Uses HTTP error handler to check status code

        """

        url = self.root_url + "/users/" + key

        data = {
                 'client_id': '{}'.format(self.client_id)
                }

        r = requests.get(url, params=data)
        http_error_handler(r.status_code)
        raw_json = r.json()
        return raw_json

    def get_user_stats_by_key(self, key):

        """Get a users stats by a userkey

        Args:
            key (string):    Takes in a user key.

        Return:
            raw_json (dict): Dictionary of the result json requested

        Raises:
            Exception error: Uses HTTP error handler to check status code

        """

        url = self.root_url + "/users/" + key + "/stats"

        data = {
                 'client_id': '{}'.format(self.client_id)
                }

        r = requests.get(url, params=data)
        http_error_handler(r.status_code)
        raw_json = r.json()
        return raw_json

    def filter_image_upload_lboards(self, bbox=None, end_time=None,
                                    iso_countries=None, per_page=200,
                                    start_time=None, userkeys=None,
                                    usernames=None):

        """Filter leaderboards on image upload

        Args:
            bbox (string): 	  Filter by the bounding box, given
                              as minx,miny,maxx,maxy. One string comma seperated.
            end_time (string): Filter images that are captured before end_time.
                               Must be a valid ISO 8601 date.
            iso_countries (string): Count images in the specified countires,
                                    given as ISO 3166 country codes.
            per_page (int):   Number of responses per page. Default is 200.
            start_time:       Filter images that are captured since start_time.
                              Must be a valid ISO 8601 date.
            userkeys:         Filter images captured by users, given as user
                              keys.
                              One string comma seperated.
            usernames:        Filter images captured by users, given as
                              usernames. One string comma seperated.

        Return:
            raw_json (dict): Dictionary of the result json requested

        Raises:
            Exception error: Uses HTTP error handler to check status code

        """

        url = self.root_url + "/leaderboard/images"

        data = {
                 'bbox': bbox,
                 'end_time': end_time,
                 'iso_countries': iso_countries,
                 'per_page': '{}'.format(per_page),
                 'start_time': start_time,
                 'userkeys': userkeys,
                 'usernames': usernames,
                 'client_id': '{}'.format(self.client_id)
                }

        r = requests.get(url, params=data)
        http_error_handler(r.status_code)
        raw_json = r.json()
        return raw_json
