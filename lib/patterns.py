from lib.TimeNode import TimeNode, TimeNodeSet
import operator

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
    
def interior(s, X1, X2,  patterns=set()):
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

def get_stars_sats(s, threshold=3):
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