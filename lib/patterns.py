from lib.TimeNode import TimeNode, TimeNodeSet
from lib.StreamProperties import *
import operator
from lib.errors import *
import copy

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
    
    def intent(self):
        """
            Returns the intent of a pattern
        """
        
        langs = [ self.support_set.label(x) for x in self.support_set.W.values() ]
        
        if langs == []:
            langs = [set()]

        return set.intersection(*langs)

    def extent(self, S=None):
        """
            Returns the extent (support set) of a pattern in a stream S
        """
        q = self.lang
        
        if S is None:
            S = (self.support_set.E, self.support_set.E)
        else:
            S = (S.E, S.E)
            
        X1 = [ TimeNode(x["u"], x["b"], x["e"]) for x in S[0] if q.issubset(set(x["label_u"]))]
        X2 = [ TimeNode(x["v"], x["b"], x["e"]) for x in S[1] if q.issubset(set(x["label_v"]))]
        
        X = X1 + X2
        X = TimeNodeSet(elements=X)
        return X
    
    def elements(self):
        return self.lang
    
    def copy(self):
        return Pattern(self.lang.copy(), self.support_set.copy())
    
    def __str__(self):
        return f"{self.lang} {self.support_set.W}"
        
    def __repr__(self):
        return self.__str__()
    
    def __eq__(self, o):
        return self.lang == o.lang and self.support_set == o.support_set
        
class BiPattern:
    """
        Bipattern class
    """
    def __init__(self, _lang=(set(), set()), _support_set=set()):
        self.lang = _lang
        self.support_set = _support_set
    
    def add(self, item, side):
        if side == 0:
            self.lang[0].add(item)
        else:
            self.lang[1].add(item)
        
    def minus(self, I):
        return set([ x for x in set(I[0]).difference(self.lang[0]) ]), set([ x for x in set(I[1]).difference(self.lang[1]) ])
    
    def intent(self):
        """
            Returns the intent of a pattern
        """
        
        langs_left = [ self.support_set.label(x) for x in self.support_set.W.values() if x.node in self.support_set._top ]
        langs_right = [ self.support_set.label(x) for x in self.support_set.W.values() if x.node in self.support_set._bot ]
        
        if langs == []:
            langs = [set()]

        return set.intersection(*langs)

    def extent(self, S=None):
        """
            Returns the extent (support set) of a pattern in a stream S
        """
        q = self.lang
        
        if S is None:
            S = (self.support_set.E, self.support_set.E)
        else:
            S = (S.E, S.E)
            
        X1 = [ TimeNode(x["u"], x["b"], x["e"]) for x in S[0] if q.issubset(set(x["label_u"]))]
        X2 = [ TimeNode(x["v"], x["b"], x["e"]) for x in S[1] if q.issubset(set(x["label_v"]))]
        
        X = X1 + X2
        X = TimeNodeSet(elements=X)
        return X
    
    def __str__(self):
        return f"{self.lang} {self.support_set.W}"
        
    def __repr__(self):
        return self.__str__()
    
    def __eq__(self, o):
        return self.lang == o.lang and self.support_set == o.support_set
    
def generic_interior(s, X1, X2,  patterns=set()):
    """
        Slower, but works for any property that defines p_1 and p2
        Use it if the property has no self defined interior function.
    """
    stsa = s.core_property
        
    S1 = TimeNodeSet()
    S2 = TimeNodeSet()

    substream = s.substream(X1, X2)
    nodes = set(substream.V) # set( list(X1.nodes()) +  list(X2.nodes()) )

    while 1:
        old_S1 = S1
        old_S2 = S2
        for u in nodes:
            p1_true, tmp = stsa.p1(u, substream)
            p2_true, tmp2 = stsa.p2(u, substream)

            if p1_true:
                for x in tmp:
                    S1.add(x)
            if p2_true:
                for x in tmp2:
                    S2.add(x)
        
        if S1 == old_S1 or S2 == old_S2:
            break

    return S1, S2

def interior(s):
    """
        Factory interior function, will attempt to call a specialized faster function,
        or will default to the generic algorithm if there is no such function
    """
    prop = s.core_property
    # print(type(prop))
    #if type(prop) is StreamProperties.StreamStarSat:
    return prop.interior(s)
    #else:
    #    raise Error

def get_stars_sats(s, threshold=1):
    """
        Interior function for star satellite, modify to return a stream instead ?
        @param s: a stream graph
        @return: two TimeNodeSets, each containing the k-stars and k-satellites of s
    """

    THRESHOLD = threshold
    stars = TimeNodeSet()
    satellites = TimeNodeSet()

    for k, u in enumerate(s.degrees):
        neigh = set()
        best_neighs = set()
        last_times = {} # {u: -1 for u in s.degrees}
        for i in sorted(s.degrees[u], key=operator.itemgetter(1, 2,-3)):
            v, t, ev_type = i[0], i[1], i[2]
            # First check if the property is true
            starsat_is_true = len(neigh) >= THRESHOLD
            
            if starsat_is_true:
                best_neighs = best_neighs.union(neigh)

            if ev_type == 1:
                neigh.add(v)
                last_times[v] = t
                if not starsat_is_true:
                    # While the property is true (typically, we have degree > THRESHOLD)
                    # u remains star, so we should not change the times
                    last_times[u] = t
            else:
                neigh.remove(v)
                if starsat_is_true:
                    stars.add(TimeNode(u, last_times[u], t))
                    for x in best_neighs:
                        # min sur le t aussi ? 
                        satellites.add(TimeNode(x, max(last_times[x], last_times[u]), t))
                    best_neighs = set()
    return stars, satellites


def bipatterns(stream, _top, _bot, s=2):
    """
        Enumerates all bipatterns
    """
    stream.EL = set()
    stream.bipatterns_list = []
    # S = interior(self, _top, _bot, set())
    S = stream.core_property.interior(stream)
    pattern = Pattern(set(), S)
    pattern.lang = pattern.intent() # Pattern(stream.intent([stream.label(x) for x in stream.W.values()]),S)
    enum(stream, pattern, set(), s=s, glob_stream=stream)

def patterns(stream, _top, _bot, s=2):  
    """
        Enumerates all patterns
    """
    stream.EL = set()
    stream.bipatterns_list = []
    # S = interior(self, _top, _bot, set())
    S = stream.core_property.interior(stream)
    pattern = BiPattern(set(), S)
    pattern.lang = pattern.intent() # Pattern(stream.intent([stream.label(x) for x in stream.W.values()]),S)
    enum(stream, pattern, set(), s=s, glob_stream=stream)

def enum(stream, pattern, EL=set(), depth=0, s=2, parent=set(), glob_stream=None):
    """
        Internal routine for pattern enumeration
    """
    
    # Pretty print purposes
    prefix = depth * 4 * ' '
    
    q = pattern.lang
    S = pattern.support_set
    
    glob_stream.bipatterns_list.append((pattern, parent))
    print(pattern, file=stream.bip_fp)
    # print(f"{q} {S}", file=stream.bip_fp)
    
    # Rewrite this in minus
    lang = S.I
    lang = [ S.label(x) for x in S.W.values() ]
    lang = [item for sublist in lang for item in list(sublist) if item not in q  and item not in S.EL ]
    candidates = set(lang)
    
    # bak variables are necessary so that deeper recursion levels do not modify the current object
    # Could be done by copy() in call ?
    q_bak = q.copy()
    S_bak = S.copy() # (S[0].copy(), S[1].copy())
#         EL_bak = EL.copy()
    
    for x in candidates:
        # S is not reduced between candidates at the same level of the search tree
        S = S_bak.copy() # (S_bak[0].copy(), S_bak[1].copy())
        q_x = q_bak.copy()

        # Add candidate to pattern
        q_x.add(x)
        p_x = Pattern(q_x, S)
        # print(q_x)
        # Support set of q_x
        X = p_x.extent(S=S)

        S_x = (X.intersection(S.W), X.intersection(S.W))
        # print(f"S_x: {S_x}")
        subs = stream.substream(S_x[0], S_x[1])
        subs.setCoreProperty(stream.core_property)
        subs.EL = stream.EL
        # S_x = interior(self, S_x[0], S_x[1], q_x) # p(S\cap ext(add(q, x)))
        S_x = subs.core_property.interior(subs)
        p_x = Pattern(q_x, S_x)
        # print(depth, len(stream.V), len(subs.V))
        # ipdb.set_trace()
        #print(f'q_x={q_x} has support set S_x = {S_x}')
        if len(p_x.support_set.W) >= s:
            p_x.lang = p_x.intent() # S_x.intent([ S_x.label(x) for x in S_x.W.values() ])
            
            if len(p_x.lang.intersection(stream.EL)) == 0 and p_x.lang != q: #(q_x != q and not (S_x[0] == S[0] and S_x[1] == S[1])):                     
                # pattern_x = Pattern(q_x, S_x)

                # print(f"{prefix} Calling enum with {pattern_x.lang} ({S_x})")
                enum(subs, p_x, stream.EL, depth+1, parent=q, glob_stream=glob_stream)
                
                # We reached a leaf of the recursion tree, add item to exclusion list
                # print(f"{prefix} Adding {x} to EL")
                stream.EL.add(x)
                
def fp_close(self):
    self.bip_fp.close()
