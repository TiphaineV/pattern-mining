from lib.TimeNode import TimeNode, TimeNodeSet

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
        
    S1 = []
    S2 = []

    substream = s.substream(X1, X2)
    nodes = set(substream.V) # set( list(X1.nodes()) +  list(X2.nodes()) )

    while 1:
        old_S1 = S1
        old_S2 = S2
        for u in nodes:
            p1_true, tmp = stsa.p1(u, substream)
            p2_true, tmp2 = stsa.p2(u, substream)

            if p1_true:
                S1 += tmp
            if p2_true:
                S2 += tmp2
        
        if S1 == old_S1 or S2 == old_S2:
            break

    Z1 = []
    Z2 = []
    for v, b, e in S1:
        Z1.append(TimeNode(v, b, e))
    for v, b, e in S2:
        Z2.append(TimeNode(v, b, e))
    return TimeNodeSet(elements=Z1), TimeNodeSet(elements=Z2)
