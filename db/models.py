"""
-----
Name: models.py
Description:
Generates Word2Vec embeddings.
-----
Author: [Diego Pilutti {1}, Hebatallah Mohamed {1}]
Licence: 
Copyright: Copyright 2020, MEMEX Project
Credits: [Sebastiano Vascon {1}, Stuart James {2}]
Affiliation: {1} Ca'Foscari University of Venice, {2} Istituto Italiano di Tecnologia 
License: BSD
Version: 2.0.0
Last Major Release Date: 31/03/2021
Maintainer: MEMEX Project
Email: contact@memexproject.eu
Status: Dev (Research)
Acknowledgment: 
This project has received funding from the European Union's Horizon 2020
research and innovation programme under grant agreement No 870743.
"""
import numpy as np
from pymagnitude import Magnitude

def avg_feature_vector(sentence, num_features = 300):
    """
	Generates Word2Vec embeddings for a text.
	
	:param sentence: text to generate embeddings for.
	:param num_features: feature vector length
	:return: embeddings feature vector
	"""
    vectors = Magnitude('models/GoogleNews-vectors-negative300.magnitude')
    words = sentence.split()
    feature_vec = np.zeros((num_features, ), dtype='float32')
    n_words = 0
    for word in words:
        feature_vec = vectors.query(word)
        n_words += 1
    if (n_words > 0):
        feature_vec = np.divide(feature_vec, n_words)
    return feature_vec

def get_emb_vect(sentence):
    """
	A wrapper to generate Word2Vec embeddings for a text.
	
	:param sentence: text to generate embeddings for.
	:return: embeddings feature vector
	"""
    return avg_feature_vector(sentence)