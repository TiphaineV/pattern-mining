import ujson as json
import sys
import logging
# from lib.StreamProperties import StreamStarSat
from lib.TimeNode import *

class Stream:
    def __init__(self, lang=set(), _loglevel=logging.DEBUG, _fp=sys.stdout):
        self.T = {}
        self.V = set()
        self.W = TimeNodeSet()
        self.E = []
        self.core_property = None
        
        self.bip_fp = _fp
        self.bipatterns_list = []
        self.EL = set()
        
        # Language
#         if type(lang) is set:
#             self.patternClass = Pattern
#         else:
#             self.patternClass = BiPattern
        
        self.I = lang
        
        # Store both degree view and links (times) view,
        # as the optimal view is different depending on the calculation
        self.degrees = {}
        self.times = {}
        
        self.logger = logging.getLogger()
        self.logger.setLevel(_loglevel)
    
    def __eq__(self, o):
        return self.T == o.T and self.V == o.V and self.W == o.W and self.E == o.E

    def nodes(self):
        # iterator on nodes ?
        return self.V
    
    def copy(self):
        stream_copy = Stream(lang=self.I, _fp=self.bip_fp)
        stream_copy.T = self.T
        stream_copy.V = self.V.copy()
        stream_copy.W = self.W.copy()
        stream_copy.E = self.E.copy()
        stream_copy.degrees = self.degrees.copy()
        stream_copy.times = self.times.copy()
        stream_copy.EL = self.EL.copy()
        stream_copy.core_property = self.core_property
        
        return stream_copy
    
    def add_link(self, l):
        u = l["u"]
        v = l["v"]
        b = l["b"]
        e = l["e"]
        label_u = l["label_u"]
        label_v = l["label_v"]

        self.V.add(u)
        self.V.add(v)
        
        # Maintain temporal adjacency list 
        try:
            self.degrees[u].append((v, b, 1, label_u))
            self.degrees[u].append((v, e, -1, label_u))
        except KeyError:
            self.degrees[u] = [(v, b, 1, label_u), (v, e, -1, label_u)]

        try:
            self.degrees[v].append((u, b, 1, label_v))
            self.degrees[v].append((u, e, -1, label_v))
        except KeyError:
            self.degrees[v] = [(u, b, 1, label_v), (u, e, -1, label_v)]

        # Maintain interaction times for each pair of nodes (u,v)
        try:
            self.times[frozenset([u,v])].append((b, e, label_u, label_v))
        except KeyError:
            self.times[frozenset([u,v])] = [ (b, e, label_u, label_v) ]
        
        # Add to E
        self.E.append(l)
    
    def setCoreProperty(self, prop):
        self.core_property = prop
    
    def add_links(self, links):
        self.E = links
        self.V = set()
        self.T = { "alpha": 0, "omega": 10 }
        
        for (i, link) in enumerate(links):
            self.V.add(link["u"])
            self.V.add(link["v"])
            
            u = link["u"]
            v = link["v"]
            b = link["b"]
            e = link["e"]
            label_u = link["label_u"]
            label_v = link["label_v"]
            
            try:
                self.degrees[u].append((v, b, 1, label_u))
                self.degrees[u].append((v, e, -1, label_u))
            except KeyError:
                self.degrees[u] = [(v, b, 1, label_u), (v, e, -1, label_u)]
                
            try:
                self.degrees[v].append((u, b, 1, label_v))
                self.degrees[v].append((u, e, -1, label_v))
            except KeyError:
                self.degrees[v] = [(u, b, 1, label_v), (u, e, -1, label_v)]
    
            try:
                self.times[frozenset([u,v])].append((b, e, label_u, label_v))
            except KeyError:
                self.times[frozenset([u,v])] = [ (b, e, label_u, label_v) ]
    
    def readStream(self, filepath):
        fp = open(filepath)
        data = json.load(fp)
        self.T = data["T"]
        self.V = set(data["V"])
        self.W = TimeNodeSet()
        self.E = []
        
        for link in data["E"]:
            t_u = TimeNode(link["u"], link["b"], link["e"], _label=link["label_u"])
            t_v = TimeNode(link["v"], link["b"], link["e"], _label=link["label_v"])
            self.W.add(t_u)
            self.W.add(t_v)
            self.add_link(link)
        
        return data
    
    def writeStream(self, name="out.json"):
        data = { "T": self.T, "V": self.V, "W": self.W, "E": self.E }
        
        json.dump(data, open(name, "w+"))
    
    def label(self, x):
        """
            Returns the label associated to an element of W
        """
        v = x.node
        b, e = x.b, x.e
        
        # Iterate over neighborhood to find label
        b_val = None
        for u, t, ev_type, label in self.degrees[v]:
            if t <= e and ev_type == 1:
                b_val = t
            if b_val is not None and ev_type == -1:
                if b_val <= e <= t:
                    return set(label)
                else:
                    b_val = None
        return set()
    
    def substream(self, W1, W2):
        # W1, W2: [(u, b,e), (v, b',e'), etc.]
        # returns a substream induced by a subset of W.
        # Only return links etc. involving W1, W2, at their resp. times
        # TODO : Update to make faster (for starters, don't iterate through all E every time)
        
        subs = Stream()
        subs.T = self.T
        subs.V = set([x.node for x in  W1 ] + [x.node for x in W2])
        W = W1.union(W2)
        subs.W = self.W.intersection(W) #  eee ?
        subs.W = TimeNodeSet(elements=subs.W)
        subs.E = []
        subs.degrees = { u: [] for u in subs.V }
        
        for l in self.E:
            # It is necessary to truncate the link if it only partially
            # intersects with subs.W
            t_u = TimeNode(l["u"], l["b"], l["e"])
            t_v = TimeNode(l["v"], l["b"], l["e"])

            cap = TimeNodeSet(elements=[t_u, t_v]).intersection(subs.W).values()

            if len(cap) == 2:
                u, v = cap[0], cap[1]

                if u.b == v.b and u.e == v.e:
                    new_l = {
                            "u":u.node,
                            "v": v.node,
                            "b": u.b,
                            "e": u.e,
                            "label_u": l["label_u"],
                            "label_v": l["label_v"],
                            }
                    subs.add_link(new_l)
        
        return subs
    
    def neighbours(self, node):
        return set([ x[0] for x in self.degrees[node] ])
    
    def __str__(self):
        edges = '\n'.join([f"({x['b']}, {x['e']}, {x['u']}, {x['v']})" for x in self.E ])
        return f"T: {self.T}\n\
V: {self.V},\n\
W: {self.W},\n\
E: {edges}\
        "
    
    def __repr__(self):
        return self.__str__()

                           
class BipartiteStream(Stream):
    def __init__(self, _loglevel=logging.DEBUG, _fp=sys.stdout):
        self.T = {}
        self.V = { "left": set(), "right": set() }
        self.W = TimeNodeSet()
        self.E = []
        self.core_property = None
        
        self.bip_fp = _fp
        self.bipatterns_list = []
        self.EL = set()
        
        # Language
#         if type(lang) is set:
#             self.patternClass = Pattern
#         else:
#             self.patternClass = BiPattern
        
        self.I = {"left": set(), "right": set()}
        
        # Store both degree view and links (times) view,
        # as the optimal view is different depending on the calculation
        self.degrees = {}
        self.times = {}
        
        self.logger = logging.getLogger()
        self.logger.setLevel(_loglevel)
    
    def __eq__(self, o):
        return self.T == o.T and self.V == o.V and self.W == o.W and self.E == o.E

    def nodes(self):
        # iterator on nodes ?
        return self.V["left"], self.V["right"]
    
    def copy(self):
        stream_copy = Stream(lang=self.I, _fp=self.bip_fp)
        stream_copy.T = self.T
        stream_copy.V = self.V.copy()
        stream_copy.W = self.W.copy()
        stream_copy.E = self.E.copy()
        stream_copy.degrees = self.degrees.copy()
        stream_copy.times = self.times.copy()
        stream_copy.EL = self.EL.copy()
        stream_copy.core_property = self.core_property
        
        return stream_copy
    
    def add_link(self, l):
        u = l["u"]
        v = l["v"]
        b = l["b"]
        e = l["e"]
        label_u = l["label"]["left"]
        label_v = l["label"]["right"]

        self.V["left"].add(u)
        self.V["right"].add(v)
        
        # Maintain temporal adjacency list 
        try:
            self.degrees[u].append((v, b, 1, label_u))
            self.degrees[u].append((v, e, -1, label_u))
        except KeyError:
            self.degrees[u] = [(v, b, 1, label_u), (v, e, -1, label_u)]

        try:
            self.degrees[v].append((u, b, 1, label_v))
            self.degrees[v].append((u, e, -1, label_v))
        except KeyError:
            self.degrees[v] = [(u, b, 1, label_v), (u, e, -1, label_v)]

        # Maintain interaction times for each pair of nodes (u,v)
        try:
            self.times[frozenset([u,v])].append((b, e, label_u, label_v))
        except KeyError:
            self.times[frozenset([u,v])] = [ (b, e, label_u, label_v) ]
        
        # Add to E
        self.E.append(l)
    
    def setCoreProperty(self, prop):
        self.core_property = prop
    
    def add_links(self, links):
        self.E = links
        self.V = { "left": set(), "right": set() }
        self.T = { "alpha": 0, "omega": 10 }
        
        for (i, link) in enumerate(links):
            self.V["left"].add(link["u"])
            self.V["right"].add(link["v"])
            
            u = link["u"]
            v = link["v"]
            b = link["b"]
            e = link["e"]
            label_u = link["label"]["left"]
            label_v = link["label"]["right"]
            
            try:
                self.degrees[u].append((v, b, 1, label_u))
                self.degrees[u].append((v, e, -1, label_u))
            except KeyError:
                self.degrees[u] = [(v, b, 1, label_u), (v, e, -1, label_u)]
                
            try:
                self.degrees[v].append((u, b, 1, label_v))
                self.degrees[v].append((u, e, -1, label_v))
            except KeyError:
                self.degrees[v] = [(u, b, 1, label_v), (u, e, -1, label_v)]
    
            try:
                self.times[frozenset([u,v])].append((b, e, label_u, label_v))
            except KeyError:
                self.times[frozenset([u,v])] = [ (b, e, label_u, label_v) ]
    
    def readStream(self, filepath):
        fp = open(filepath)
        data = json.load(fp)
        self.T = data["T"]
        self.V = {"left": set(data["V"]["left"]), "right": set(data["V"]["right"]) }
        self.W = TimeNodeSet()
        self.I = data["I"]
        self.I["left"] = set(self.I["left"])
        self.I["right"] = set(self.I["right"])
        
        self.E = []
        
        for link in data["E"]:
            t_u = TimeNode(link["u"], link["b"], link["e"], _label=link["label"]["left"])
            t_v = TimeNode(link["v"], link["b"], link["e"], _label=link["label"]["right"])
            self.W.add(t_u)
            self.W.add(t_v)
            self.add_link(link)
        
        return data
    
    def writeStream(self, name="out.json"):
        data = { "settings": {}, "I": self.I, "T": self.T, "V": self.V, "W": self.W, "E": self.E }
        
        json.dump(data, open(name, "w+"))
    
    def label(self, x):
        """
            Returns the label associated to an element of W
        """
        v = x.node
        b, e = x.b, x.e
        
        # Iterate over neighborhood to find label
        b_val = None
        for u, t, ev_type, label in self.degrees[v]:
            if t <= e and ev_type == 1:
                b_val = t
            if b_val is not None and ev_type == -1:
                if b_val <= e <= t:
                    return set(label)
                else:
                    b_val = None
        return set()
    
    def substream(self, W1, W2):
        # W1, W2: [(u, b,e), (v, b',e'), etc.]
        # returns a substream induced by a subset of W.
        # Only return links etc. involving W1, W2, at their resp. times
        # TODO : Update to make faster (for starters, don't iterate through all E every time)
        
        subs = BipartiteStream()
        subs.T = self.T
        subs.V["left"] = set([x.node for x in  W1 if x.node in self.V["left"] ] + [x.node for x in W2 if x.node in self.V["left"] ])
        subs.V["right"] = set([x.node for x in  W1 if x.node in self.V["right"] ] + [x.node for x in W2 if x.node in self.V["right"] ])
        W = W1.union(W2)
        subs.W = self.W.intersection(W) #  eee ?
        subs.W = TimeNodeSet(elements=subs.W)
        subs.E = []
        subs.degrees = { u: [] for u in list(subs.V["left"]) + list(subs.V["right"]) }
        
        for l in self.E:
            # It is necessary to truncate the link if it only partially
            # intersects with subs.W
            t_u = TimeNode(l["u"], l["b"], l["e"])
            t_v = TimeNode(l["v"], l["b"], l["e"])
            label_left = set(l["label"]["left"])
            label_right = set(l["label"]["right"])

            cap = TimeNodeSet(elements=[t_u, t_v]).intersection(subs.W).values()

            if len(cap) == 2:
                u, v = cap[0], cap[1]

                if u.b == v.b and u.e == v.e:
                    new_l = {
                        "u":u.node,
                        "v": v.node,
                        "b": u.b,
                        "e": u.e,
                        "label": {
                            "left": label_left,
                            "right": label_right
                        }
                    }
                    subs.I["left"] = subs.I["left"].union(label_left)
                    subs.I["right"] = subs.I["right"].union(label_right)
                    subs.add_link(new_l)
        
        return subs
    
    def neighbours(self, node):
        return set([ x[0] for x in self.degrees[node] ])
    
    def __str__(self):
        edges = '\n'.join([f"({x['b']}, {x['e']}, {x['u']}, {x['v']})" for x in self.E ])
        return f"T: {self.T}\n\
V: {self.V},\n\
W: {self.W},\n\
E: {edges}\
        "
    
    def __repr__(self):
        return self.__str__()