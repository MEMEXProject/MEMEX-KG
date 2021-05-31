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
import torch
from torchvision import models
import torch.nn as nn

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

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


def get_visual_model(name):
    model = None
    if name == 'ResNet101':
        cnn = models.resnet101(pretrained=True)
        # Remove final layer and add pool
        model = nn.Sequential(*list(cnn.children())[:-2] + [nn.AdaptiveAvgPool2d( output_size=(2, 2)) ]).to(device)
    if name == 'ResNet18':
        cnn = models.resnet18(pretrained=True)
        # Remove final layer and add pool
        model = nn.Sequential(*list(cnn.children())[:-2] + [nn.AdaptiveAvgPool2d( output_size=(2, 2)) ]).to(device)
    if model:
        model = model.eval()
    return model


def prepare_image_from_file(image_path,image_max_dim=224):
    """
	Prepares image loading and normalising the mean standard deviation
    returns a torch tensor
	
	:param image_path: file path of the image
    :param image_max_dim: macimum width/height (normally 224)
	:return: torch tensor [B, C, W, H]
	"""
    
    ''' Scales, crops, and normalizes a PIL image for a PyTorch model,
        returns an Numpy array
    '''
    from PIL import Image
    try:
        pil_image = Image.open(image_path).convert('RGB')
    except:
        return None
    return prepare_image(pil_image,image_max_dim )

 
def prepare_image(image, image_max_dim=224):
    pil_image = image 
    # Resize keeping longest side
    width, height = pil_image.size
    aspect_ratio = width / height
    if aspect_ratio > 1:
        pil_image = pil_image.resize((round(aspect_ratio * image_max_dim), image_max_dim))
    else:
        pil_image = pil_image.resize((image_max_dim, round(image_max_dim * aspect_ratio)))
    
    # Convert color channels to 0-1
    np_image = np.array(pil_image) / 255

    # Normalize the image
    np_image = (np_image - np.array([0.485, 0.456, 0.406])) / np.array([0.229, 0.224, 0.225])
    
    # Reorder dimensions
    np_image = np_image.transpose((2, 0, 1))

    # Convert to torch
    I = torch.from_numpy(np_image).unsqueeze(0).float().to(device)
    
    return I

def get_visal_embedding(model, image):
    d = model(image).view(-1).cpu().detach()
    return d.numpy()