from lib.TimeNode import Interval, TimeNode, TimeNodeSet

class StreamProperty():
    def __init__(self, stream):
        self.S = stream
        
    def p1(self):
        return True

    def p2(self):
        return True

class BHACore(StreamProperty):
    def __init__(self, stream):
        super(BHACore, self).__init__(stream)
        self.h = 2
        self.a = 2
        
    def p1(self, x, Z1, Z2, pattern): 
        subg = self.G.subgraph(Z1.union(Z2))
        degree = subg.out_degree(x)
        pattern = pattern.issubset(self.G.node[x]["lang"])
        
        return degree >= self.h and pattern
        
    def p2(self, x, Z1, Z2, pattern):
        subg = self.G.subgraph(Z1.union(Z2))
        degree = subg.in_degree(x)
        pattern = pattern.issubset(self.G.node[x]["lang"])
        
        return degree >= self.a and pattern

class StreamStarSat(StreamProperty):
    
    def __init__(self, stream, threshold=3):
        super().__init__(stream)
        self.star_degree = threshold

        self.stars = {}
        self.sat = {}
        
        self.get_stars_sats(stream)
        
    
    def get_stars_sats(self, s):
        """
            @param s: a stream graph
            @return: two TimeNodeSets, each containing the k-stars and k-satellites of s
        """

        THRESHOLD = self.star_degree
        stars = TimeNodeSet()
        satellites = TimeNodeSet()

        for u in s.degrees:
            neigh = set()
            best_neighs = set()
            last_times = {u: -1 for u in s.degrees}
            for i in sorted(s.degrees[u], key=operator.itemgetter(1, 2,-3)):
                v, t, ev_type = i[0], i[1], i[2]
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
                            satellites.add(TimeNode(x, last_times[x], t))
                        best_neighs = set()
        return stars, satellites
        
        
    def p1(self, u, substream): # Star
        if self.substream is None or substream != self.substream:
            self.substream = substream
            self.get_stars_sat(u)
        return True, self.stars
        # if self.stars is not None:
        #    return True, self.stars
        
        return True, self.stars
    
    def p2(self, u, substream): # Sat
        if self.substream is None or substream != self.substream:
            self.substream = substream
            self.get_stars_sat(u)
        return True, self.sat
    
    