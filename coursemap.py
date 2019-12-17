from stanfordclasses import StanfordClass
import pickle
import networkx as nx

with open('stanfordclasslist.pkl', 'rb') as f:
    StanfordClassList = pickle.load(f)
f.close()

coursemap = nx.DiGraph()
