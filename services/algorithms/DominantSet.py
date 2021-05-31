"""
-----
Name: DominantSet.py
Description:
Handles the Dominant Set clustering.
-----
Author: Christian Cabrera {1}
Licence: 
Copyright: Copyright 2020, MEMEX Project
Credits: [Sebastiano Vascon {1}]
Affiliation: {1} Ca'Foscari University of Venice
License: BSD
Version: 3.0.0
Last Major Release Date: 31/05/2021
Maintainer: MEMEX Project
Email: contact@memexproject.eu
Status: Dev (Research)
Acknowledgment: 
This project has received funding from the European Union's Horizon 2020
research and innovation programme under grant agreement No 870743.
"""
import scipy.linalg as la
import networkx as nx
import numpy as np
import community

class DominantSet_Clustering():
    """
    DominantSet_Clustering handles the Dominant Set clustering introduced in "Dominant sets and pairwise clustering." IEEE transactions on pattern analysis and machine intelligence 29.1 (2006): 167-172.
    
    """    
    def __init__(self, Graph, epsilon=1.0e-4,
                 cutoff=1.0e-5, binary=False):
        self.epsilon = epsilon
        self.cutoff = cutoff
        self.isbinary = binary
        self.adj_matrix = None
        self.Graph = Graph
        self.labels = list(Graph.nodes(data="label", default="Not Available"))
        self.coherence = None
        self.clusters = None
        self.clusters_labels = None
        self.groupedClusters = None
        self.modularity = None
        self.distance_matrix = None
        
    def mapCluster_to_label(self, Cluster_Gnx, labels_list):
        """
        Map clusters to node labels.
        
        :return: dict of cluster labels.
                
        """        
        index = 0
        cluster_labels = {}
        cluster_list = list()
        for i in labels_list:
            for j in Cluster_Gnx.keys():
                if index in Cluster_Gnx[j]['nodes']:
                    cluster_labels[i[0]] = int(j)
                    cluster_list.append(int(j))
                    break
            index += 1
        return cluster_labels    
  
    def DominantSet(self, A):
        """
        Dominant Set object constructor.
        :param adj: graph adjacency matrix.
                
        """      
        x = np.ones(A.shape[0]) / float(A.shape[0])
        distance = self.epsilon * 2
        cohe = 0
        maxiters = 2500
        iters = 0
        while distance >= self.epsilon and iters < maxiters: # repeat until convergence (dist < epsilon means convergence)
            x_old = x.copy() # apply replicator dynamics
            x = x * A.dot(x) # Cohesiviness cluster.
            cohe = x.sum()
            x = x / cohe
            distance = np.linalg.norm(x - x_old)
            iters += 1
        return x, cohe

    def clustering(self):
        """
        Performs the DS clustering.
        
        """        
        C = {}
        dsCount = 0
        if self.adj_matrix is None:
            self.get_adj_matrix()

        A = self.adj_matrix
        X = np.arange(len(A))

        S = A

        listCohe = list()
        # repeat until all objects have been clustered
        while S.size > 1:

            C[str(dsCount)] = {}
            tempIndex = list()
            valuesIndex = list()
            x_dict = {}
            
            x, cohe = self.DominantSet(A=S)
            
            for i in range(len(x)):
                x_dict.update({X[i]:x[i]})
            sorted_x = sorted(x_dict.items(), key=lambda x: x[1], reverse=True)    
    
            listCohe.append(cohe)
            # cutoff = np.median(x[x>0])
            dom_idx = x < self.cutoff

            # those elements whose value is <= cutoff are the ones belonging to the cluster just found
            # on x are their partecipating values (carateristic vector)

            # create positional index and values
            for i in range(len(dom_idx)):
                if (dom_idx[i] == 0):
                    tempIndex.append(i)
                    # valuesIndex.append(X[i])

            index = np.array(tempIndex)
          
            # add sorted cluster nodes
            for dic_item in sorted_x:
                ind = dic_item[0]
                if ind in tempIndex:
                    valuesIndex.append(ind)        
                            
            valuesIndex = np.array(valuesIndex)
            C[str(dsCount)]['nodes'] = valuesIndex

            S = S[dom_idx, :][:, dom_idx] # remove elements of cluster just found, from matrix
            X = np.delete(X, index)

            #print("Cluster:" + str(dsCount) + " N.Elements:" + str(len(valuesIndex)) + " Remaining:" + str(len(S)))
            #print()

            dsCount += 1

        if (len(X) > 0):
            C[str(dsCount)] = {}
            C[str(dsCount)]['nodes'] = X

        self.clusters = C
        self.coherence = listCohe
        self.clusters_labels = self.mapCluster_to_label(self.clusters, self.labels)
        self.labels = list(self.clusters_labels.values())
        return self.clusters, self.coherence, self.clusters_labels

    def constrain_ds(self, G, target, adj = None):
        """
        Constrain the DS based on a seed node.
        
        :param G: the graph to be clustered with constrained DS.
        :param target: the seed node.
        :param adj: graph adjacency matrix.
        """        
        if adj is None:
            adj = (nx.adjacency_matrix(G)).todense()
            adj = np.squeeze(np.asarray(adj))

        A = adj.clip(min=0)
        n = len(A)
        B = A.copy()

        for i in target:
            B = np.delete(B, i, axis=0)
            B = np.delete(B, i, axis=1)

        I = np.zeros((n, n))
        np.fill_diagonal(I, 1)

        for i in target:
            I[i, i] = 0

        eigValues, _ = la.eig(B)
        alpha = max(eigValues.real) + 0.01

        aI = alpha * I
        W = A - aI
        minAlpha = np.full((n, n), alpha)

        W = W + minAlpha

        self.adj_matrix = W

        return

    def save_adjacency(self, path):
        """
        Save adjacency matrix into a file.
        
        :param path: 'str' location of the file 
        """ 
        with open(path, 'wb') as f:
            np.save(f, self.adj_matrix)

    def load_adjacency(self, file):
        """
        Load adjacency matrix from a file.
        
        :param path: 'str' location of the file to be loaded
        """ 
        with open(file, 'rb') as f:
            distances = np.load(f, allow_pickle=True)
            self.adj_matrix = distances
            
    def setDominantSet(self, path):
        """
        Saves a graphml with the Dominant set labels.
        
        :param path: 'str' location of the file
        """ 
        nx.set_node_attributes(self.Graph, self.clusters_labels, 'DS')
        nx.write_graphml(self.Graph, path + 'DS.graphml', named_key_ids=True)

    def evaluate(self):
        """
        Computes the modularity.
        
        :return: modularity
        """ 
        modularity = community.modularity(self.clusters_labels, self.Graph)
        self.modularity = modularity
        #x = internalValidation(self.adj_matrix, labels)
        return self.modularity