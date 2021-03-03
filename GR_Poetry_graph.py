import os
import sys
import ujson as json
from lib.Graph import BipartiteGraph, Graph, StarSat, BHACore, bigraph_patterns, graph_patterns
import networkx as nx
import matplotlib.pyplot as plt
import logging
import math
from sklearn.feature_extraction.text import TfidfVectorizer

import nltk
from nltk.corpus import words

# nltk.download("punkt")
nltk.download("words")
word_corpus = set(words.words())

def create_json():
    # Books attributes
    books_file = open("data/goodreads/goodreads_books_poetry.json")
    books = {}
    has_reviews = 0
    attr_lang = {}
    attr_bip = {}

    data_graph = {  "V": { "left": [], "right": []},
                    "I": { "left": [], "right": []},
                    "E": []
                 }

    for (i, line) in enumerate(books_file):
        data = json.loads(line)
        # We add "B-" prefixing each attribute to avoid language duplicates between books and users
        book_attributes = [ "B-" + x.strip() for x in map(str.lower, data["description"].split(" ")) if x.strip() in word_corpus ]
        book_id = "B-" + data["book_id"]
        books[book_id] = book_attributes
        
    ###### Reviews attributes
    reviews_file = open("data/goodreads/goodreads_reviews_poetry.json")
    reviews = []
    users_ids = set()
    books_ids = set()
    labels_users = []
    labels_books = []
    ratings = {} # sparse matrix ?
    links = []
    min_date_added = None

    for (i,line) in enumerate(reviews_file):
        
        data = json.loads(line)
        
        user_id = "U-" + data["user_id"]
        book_id = "B-" + data["book_id"]
        
        attr_bip[user_id] = 1
        attr_bip[book_id] = 0

        reviews.append(data["review_text"])
        
        u = user_id
        v = book_id

        # Pick first 5 words of review and description for each node -- FOR TESTS ONLY --
        # map to lowercase
        label_u = [ "U-" + x.strip() for x in map(str.lower, set(data["review_text"].split(" "))) if x.strip() in word_corpus ]
        label_v = list(set(books[v]))
        
        # Sanity check to make sure we add everything consistently
        assert(("U-" in u and all(["U-" in x for x in label_u])) or ("B-" in u and all(["B-" in x for x in label_u])))
        assert(("U-" in v and all(["U-" in x for x in label_v])) or ("B-" in v and all(["B-" in x for x in label_v])))

        # To keep track of all the language elements (I)
        labels_users.extend(label_u)
        labels_books.extend(label_v)

        # Create keys if not seen before
        if u not in attr_lang:
            attr_lang[u] = label_u
        if v not in attr_lang:
            attr_lang[v] = label_v

        attr_lang[u].extend(label_u)
        attr_lang[v].extend(label_v)
        link = {"u": u, "v": v }
        links.append(link)


    data_graph["V"] = [ {"id": x, "bipartite": attr_bip[x], "label": attr_lang[x] } for x in attr_bip ]
    data_graph["I"] = {"left": list(set(labels_books)), "right": list(set(labels_users))}
    data_graph["E"] = links

    # Dump to json
    fp_out = open("grp-graph.json", "w+")
    json.dump(data_graph, fp_out)
    fp_out.close()

# Read from json
if not os.path.isfile("grp-graph.json"):
    print("Woop woop! Let's build the graph...")
    create_json()
graph_data = json.load(open("grp-graph.json"))

# Prepare graph
edges = [ (x["u"], x["v"]) for x in graph_data["E"] ]
bip_graph = BipartiteGraph(edges, lang=(set(graph_data["I"]["left"]), set(graph_data["I"]["right"])))
attr = { x["id"]: set(x["label"]) for x in graph_data["V"] }
attr_bip = { x["id"]: int(x["bipartite"]) for x in graph_data["V"] }
nx.set_node_attributes(bip_graph, attr, "lang")
nx.set_node_attributes(bip_graph, attr_bip, "bipartite")
top, bot = set([ x["id"] for x in graph_data["V"] if x["bipartite"] == 0 ]), set([  x["id"] for x in graph_data["V"] if x["bipartite"] == 0 ])
prop = BHACore(bip_graph, h=5, a=5)
bigraph_patterns(bip_graph, prop=prop)

fp = open("res.json", "w+")
for x in bip_graph.pattern_list:
    json.dump(x.json(), fp)
fp.close()
