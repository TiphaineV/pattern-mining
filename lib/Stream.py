import sys
import ujson as json
import logging
from lib.StreamProperties import StreamStarSat
from lib.TimeNode import *
from lib.patterns import *


class Stream:
    def __init__(self, lang=set(), _loglevel=logging.DEBUG, _fp=sys.stdout):
        self.T = {}
        self.V = []
        self.W = {} # TimeNodeSet
        self.E = {}
        self.core_property = None
        
        self.bip_fp = _fp
        self.EL = set()
        
        # Language
        if type(lang) is set:
            self.patternClass = Pattern
        else:
            self.patternClass = BiPattern
        
        self.I = lang
        
        # Store both degree view and links (times) view,
        # as the optimal view is different depending on the calculation
        self.degrees = {}
        self.times = {}
        self.subs = None
        
        self.logger = logging.getLogger()
        self.logger.setLevel(_loglevel)
    
    def nodes(self):
        return self.V
    
    def add_link(self, l):
        u = l["u"]
        v = l["v"]
        b = l["b"]
        e = l["e"]
        label_u = l["label_u"]
        label_v = l["label_v"]

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
        self.V = data["V"]
        self.E = []
        
        for link in data["E"]:
            self.add_link(link)
        
        return data
    
    def writeStream(self):
        data = { "T": self.T, "V": self.V, "W": self.W, "E": self.E }
        
        json.dump(data, open("./out.json", "w+"))
    
    def label(self, x):
        """
            Returns the label associated to an element of W
        """
        v = x.node
        b, e = x.b, x.e
        
        # Iterate over neighborhood to find label
        for u, t, ev_type, label in self.degrees[v]:
            if t >= b and ev_type == 1:
                return set(label)
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
        subs.W = self.W.intersection(W)
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

    def extent(self, q):
        """
            Returns the extent (support set) of a pattern
        """
        
        # Way too slow, no need to go through whole E each time...
        X1 = [ TimeNode(x["u"], x["b"], x["e"]) for x in self.E if q.issubset(set(x["label_u"]))]
        X2 = [ TimeNode(x["v"], x["b"], x["e"]) for x in self.E if q.issubset(set(x["label_v"]))]
        
        X = X1 + X2
        X = TimeNodeSet(elements=X)
        return X
    
    def intent(self, langs):
        """
            Returns the intent of a pattern
        """
        
        if langs == []:
            langs = [set()]

        return set.intersection(*langs)
    
    def bipatterns(self, _top, _bot):
        """
            Enumerates all bipatterns
        """
        self.EL = set()
        S = interior(self, _top, _bot, set())
        pattern = Pattern(self.intent([self.label(x) for x in S[0].union(S[1]).values()]),
                          S)
        self.enum(pattern, set())
        
    def enum(self, pattern, EL=set(), depth=0):
        # Value passing is strange, especially when computing the intent;
        # This causes candidates to be instantly discarded, and so 
        # the next iteration repeats indefinitely with the same number of candidates.
        
        # Pretty print purposes
        prefix = depth * 4 * ' '
        
        
        s = 2
        
        q = pattern.lang
        S = pattern.support_set
        
        # print(f"{q} {S}", file=self.bip_fp)
        print(f"{prefix} {q} {S}", file=self.bip_fp)

        
        candidates = [ x for x in pattern.minus(self.I) if not x in EL]
        # print(f'{prefix} {len(candidates)} candidates {candidates}')
        #print(f'{len(EL)} {EL}')
        #print("\n")
        
        # bak variables are necessary so that deeper recursion levels do not modify the current object
        # Could be done by copy() in call ?
        q_bak = q.copy()
        S_bak = (S[0].copy(), S[1].copy())
#         EL_bak = EL.copy()
        
        for x in candidates:
            # S is not reduced between candidates at the same level of the search tree
            S = (S_bak[0].copy(), S_bak[1].copy())

            # Add 
            q_x = q_bak.copy()
            # print(f"{prefix} Adding {x} to {q_x}")
            q_x.add(x)
            # print(q_x)
            # Support set of q_x
            X = self.extent(q_x)

            S_x = (X.intersection(S[0]), X.intersection(S[1]))
            S_x = self.interior(S_x[0], S_x[1], q_x) # p(S\cap ext(add(q, x)))
             
            # print(S_x)
            # print(f'q_x={q_x} has support set S_x = {S_x}')
            # print(f"S_x {S_x}")
            if len(S_x[0].union(S_x[1])) >= s:
                
                q_x = self.intent([ self.label(x) for x in S_x[0].union(S_x[1]).values() ])
                if len(q_x.intersection(self.EL)) == 0 and (q_x != q or S_x != S): # q_x != q is really what needed ??
                    pattern_x = Pattern(q_x, S_x)
                    # print(f"{prefix} Calling enum with {pattern_x.lang} ({S_x})")
                    self.enum(pattern_x, self.EL, depth+1)
                    
                    # We reached a leaf of the recursion tree, add item to exclusion list
                    # print(f"{prefix} Adding {x} to EL")
                    
                    self.EL.add(x)
                    
    def fp_close(self):
        self.bip_fp.close()
