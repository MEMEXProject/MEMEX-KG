#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pymapillary import Mapillary

import unittest
import os

# Insert your own key as a string here
API_KEY = os.environ['MAPILLARY_KEY']
#API_KEY

class TestMapillaryMethods(unittest.TestCase):

    def test_get_pagnation_resources(self):
        map = Mapillary(API_KEY)

        page_num = 1
        per_page = 1

        raw_json = map.get_pagnation_resources(page_num=page_num,
                                               per_page=per_page)

        # Since the page can change, I just check if a request just went through
        features_json = raw_json['features']
        self.assertEqual(type([]), type(features_json))

    def test_search_images(self):
        map = Mapillary(API_KEY)

        bbox = "16.430300,7.241686,16.438757,7.253186"
        per_page = 1

        raw_json = map.search_images(bbox=bbox, per_page=per_page)
        features_json = raw_json['features']

        # The json's is in a list
        for features in features_json:
            coordinate = features['geometry']['coordinates']

        self.assertEqual([16.432976, 7.249027], coordinate)

    def test_get_image_feature_by_key(self):
        map = Mapillary(API_KEY)

        key = "LwrHXqFRN_pszCopTKHF_Q"

        raw_json = map.get_image_feature_by_key(key=key)

        properties_ca_angle = raw_json['properties']['ca']

        self.assertEqual(323.0319999999999, properties_ca_angle)

    def test_search_sequences(self):
        map = Mapillary(API_KEY)

        userkeys = "AGfe-07BEJX0-kxpu9J3rA"
        per_page = 1

        raw_json = map.search_sequences(userkeys=userkeys, per_page=per_page)
        type_json = raw_json['type']

        self.assertEqual("FeatureCollection", type_json)

    def test_get_sequence_by_key(self):
        map = Mapillary(API_KEY)

        key = "cHBf9e8n0pG8O0ZVQHGFBQ"

        raw_json = map.get_sequence_by_key(key=key)

        properties_captured_at_json = raw_json['properties']['captured_at']

        self.assertEqual("2016-03-14T13:44:37.206Z", properties_captured_at_json)

    def test_search_changesets(self):
        map = Mapillary(API_KEY)

        types = "location"
        per_page = 1 # default is 200

        raw_json = map.search_changesets(types=types, per_page=per_page)

        for i in raw_json:
            type_json = i['type']

        self.assertEqual("location", type_json)

    def test_get_changeset_by_key(self):
        map = Mapillary(API_KEY)

        key = "obWjkY7TGbstLRNy1qYRD7"

        raw_json = map.get_changeset_by_key(key=key)

        type_json = raw_json['type']

        self.assertEqual("location", type_json)

    def test_search_users(self):
        map = Mapillary(API_KEY)

        userkeys = "HvOINSQU9fhnCQTpm0nN7Q"
        per_page = 1 # default is 200

        raw_json = map.search_users(userkeys=userkeys, per_page=per_page)

        for i in raw_json:
            username_json = i['username']

        self.assertEqual("maning", username_json)

    def test_get_user_by_key(self):

        map = Mapillary(API_KEY)

        key = "2BJl04nvnfW1y2GNaj7x5w"

        raw_json = map.get_user_by_key(key=key)

        username_json = raw_json['username']

        self.assertEqual("gyllen", username_json)

    def test_get_user_stats_by_key(self):

        map = Mapillary(API_KEY)

        key = "2BJl04nvnfW1y2GNaj7x5w"

        raw_json = map.get_user_stats_by_key(key=key)

        user_key_json = raw_json['user_key']

        self.assertEqual("2BJl04nvnfW1y2GNaj7x5w", user_key_json)

    def test_filter_image_upload_lboards(self):

        map = Mapillary(API_KEY)

        iso_countries = "SE" # given as ISO 3166 country codes.
        per_page = 1

        raw_json = map.filter_image_upload_lboards(iso_countries=iso_countries, per_page=per_page)

        for i in raw_json:
            username_json = i['username']

        self.assertEqual("roadroid", username_json)

if __name__ == '__main__':
    unittest.main()
