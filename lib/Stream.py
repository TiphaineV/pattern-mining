import sys
import ujson as json
import logging
from lib.StreamProperties import StreamStarSat

class Pattern:
    """
        Monopattern class
    """
    def __init__(self, _lang=set(), _support_set=set()):
        self.lang = _lang
        self.support_set = _support_set
    
    def add(self, item):
        self.lang.add(item)
        
    def minus(self, I):
        return set([ x for x in set(I).difference(self.lang) ])
        
class BiPattern:
    """
        Bipattern class
    """
    def __init__(self, _lang=(set(), set()), _support_set=(set(), set())):
        self.lang = _lang
        self.support_set = _support_set
    
    def add(self, item, side=0):
        # _q = (self.intent[0].copy(), self.intent[1].copy())
        self.lang[side].add(item)
    
    def minus(self, I):
        """
            Returns the candidates for extension
        """
        candidates_left = [(x, 0) for x in set(I[0]).difference(self.lang[0]) ]
        candidates_right = [(x, 1) for x in set(I[1]).difference(self.lang[1]) ]
        
        return set(candidates_left + candidates_right)

class TimeNode:
    """
        For later refactoring
    """
    def __init__(self, _node, _b, _e, _label=set()):
        self.node = _node
        self.b = _b
        self.e = _e
        self.label = _label
        
    def __str__(self):
        return f"{self.node} [{self.b}, {self.e}]"

    def __repr__(self):
        return self.__str__()
    
    def __eq__(self, o):
        return  self.node == o.node\
                and self.b == o.b\
                and self.e == o.e
    def __hash__(self):
        return hash((self.node, self.b, self.e))
        
class Stream:
    def __init__(self, lang=set(), _loglevel=logging.DEBUG, _fp=sys.stdout):
        self.T = {}
        self.V = []
        self.W = {}
        self.E = {}
        self.core_property = None
        
        self.bip_fp = _fp
        
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
        self.E = data["E"]
        
        for link in self.E:
            self.add_link(link)
        
        return data
    
    def writeStream(self):
        data = { "T": self.T, "V": self.V, "W": self.W, "E": self.E }
        
        json.dump(data, open("./out.json", "w+"))
    
    def label(self, x):
        """
            Returns the label associated to an element of W
        """
        v = x[0]
        b, e = x[1], x[2]
        
        # Iterate over neighborhood to find label
        for u, t, ev_type, label in self.degrees[v]:
            if b >= t and ev_type == 1:
                return set(label)
        return set()
    
    def substream(self, W1, W2):
        # W1, W2: [(u, b,e), (v, b',e'), etc.]
        # returns a substream induced by a subset of W.
        # Only return links etc. involving W1, W2, at their resp. times
        # Careful to return degrees etc. too !!
        
        subs = Stream()
        subs.T = self.T
        subs.V = set([x[0] for x in  W1 ] + [x[0] for x in W2])
        subs.W = set(list(W1) + list(W2))
        subs.E = []
        subs.degrees = { u: [] for u in subs.V }
        
        for l in self.E:
            if l["u"] in subs.V and l["v"] in subs.V :
                subs.add_link(l)
                subs.E.append(l)
        
        return subs
    
    def neighbours(self, node):
        return set([ x[0] for x in self.degrees[node] ])
    
    def interior(self, X1, X2,  patterns=set()):
        stsa = self.core_property
        
        S1 = []
        S2 = []

        nodes = set([ x[0] for x in X1 ] + [ x[0] for x in X2 ])

        while 1:
            old_S1 = S1
            old_S2 = S2
            for u in nodes:
                _, tmp = stsa.p1(u, X1, X2, patterns)
                __, tmp2 = stsa.p2(u, X1, X2, patterns)

                if _ :
                    S1 += tmp
                if __ :
                    S2 += tmp2
            
            if S1 == old_S1 or S2 == old_S2:
                break
                
        return set(S1), set(S2)

    def extent(self, q):
        """
            Returns the extent (support set) of a pattern
        """
        
        # Way too slow, no need to go through whole E each time...
        X1 = [ (x["u"], (x["b"], x["e"])) for x in self.E if q.issubset(set(x["label_u"]))]
        X2 = [ (x["v"], (x["b"], x["e"])) for x in self.E if q.issubset(set(x["label_v"]))]
        
        X = set(X1 + X2)
        return X, X
    
    def intent(self, langs):
        """
            Returns the intent of a pattern
        """
        
        if langs == []:
            langs = [set()]

        return set.intersection(*langs)
    
    def intersect(self, i, j):
        # returns the intersection of two time intervals, or -1 is it is void
        # does not make any asumption obout the order of the intervals, however
        # both i and j *are* intervals (i.e. e >= b, and f >= c)
        # TODO: extend to list of intervals
        b, e = i
        c, f = j

        # Disjoint
        if c >= e or f <= b:
            return None
        # Inclusion
        if (c >= b and f <= e) or \
           (b >= c and e <= f):
                return (max(b,c), min(e,f))

        # intersection
        if (c <= b and f >= b and f <= e) or\
           (b <= c and e >= c and e <= f):
            return (max(b,c), min(e,f))

        return ()
    
    def bipatterns(self, _top, _bot):
        """
            Enumerates all bipatterns
        """
        S = self.interior(_top, _bot, set())
        pattern = Pattern(self.intent([self.label(x) for x in S[0].union(S[1])]),
                          S)
        self.enum(pattern, set())
        
    def enum(self, pattern, EL=set(), depth=0):
        # Value passing is strange, especially when computing the intent;
        # This causes candidates to be instantly discarded, and so 
        # the next iteration repeats indefinitely with the same number of candidates.
        
        
        # if depth > 2:
        #    return
        
        s = 2
        
        q = pattern.lang
        S = pattern.support_set
        
        print(f"{q} {S}", file=self.bip_fp)

        candidates = [ x for x in pattern.minus(self.I) if not x in EL]
        #print(f'{len(candidates)} candidates {candidates}')
        #print(f'{len(EL)} {EL}')
        #print("\n")
        
        # bak variables are necessary so that deeper recursion levels do not modify the current object
        # Could be done by copy() in call ?
        q_bak = q.copy()
        S_bak = (S[0].copy(), S[1].copy())
        EL_bak = EL.copy()
        
        for x in candidates:
            # S is not reduced between candidates at the same level of the search tree
            S = (S_bak[0].copy(), S_bak[1].copy())

            # Add 
            q_x = q_bak.copy()
            # print(f"Adding {x} to {q_x}")
            q_x.add(x)
            # Support set of q_x
            X1, X2 = self.extent(q_x)
            # S_x = self.interior(S[0], S[1], q_x) # interior(S \cap ext(q))
            S_x = self.interior(X1, X2, q_x)
            # print(S_x)
            # print(f'q_x={q_x} has support set S_x = {S_x}')
            if len(S_x[0].union(S_x[1])) >= s:
                
                q_x = self.intent([ self.label(x) for x in S_x[0].union(S_x[1]) ])
                if len(q_x.intersection(EL_bak)) == 0 and q_x != q:
                    pattern_x = Pattern(q_x, S_x)
                    # print(f"Calling enum with {pattern_x.lang} ({q_x})")
                    self.enum(pattern_x, EL, depth+1)
                    
                    # We reached a leaf of the recursion tree, add item to exclusion list
                    self.logger.debug(f"Adding {x} to EL\n")
                    EL.add(x)