from lib.TimeNode import Interval, TimeNode, TimeNodeSet
from lib.Stream import Stream
from operator import itemgetter

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

class StreamBHACore(StreamProperty):
    def __init__(self, stream, h=2, a=2):
        super().__init__(stream)
        self.h = h
        self.a = a
        # Ensure that BipartiteStream ?
        
    
    def find_bicore(self, stream):

        # print("<================ bicore")
        # print(stream)

        hubs = TimeNodeSet()

        for u in stream.degrees:
            # print(f"Node {u}")
            if u in stream.V["left"]:
                threshold = self.h
            if u in stream.V["right"]:
                threshold = self.a

            neighbourhood = set()
            last_t = {}

            for v,t,e_type,label in sorted(stream.degrees[u], key=itemgetter(1)):
                # print([(v, t, e_type) for v,t, e_type, label in sorted(stream.degrees[u], key=itemgetter(1))])
                # print(f"linked with {v,t,e_type}")
                if e_type == 1:
                    # print(f"We add {t,v} to the neighbourhood.")
                    neighbourhood.add(v)
                    last_t[u] = t
                    last_t[v] = t
                elif e_type == -1:
                    # print(f"{u} has {len(neighbourhood)} neighbours.")
                    if len(neighbourhood) >= threshold:
                        # print(u, len(neighbourhood), last_t[u], t)
                        # print(f"We add {u} [{last_t[u]}, {t}] to hubs.")
                        hubs.add(TimeNode(u, last_t[u], t))
                        # We have no idea about v's neighbourhood.
                        # hubs.add(TimeNode(v, last_t[v], t))
                    # print(f"We remove {t, v} from neighbourhood.")
                    # print(f"{u}")
                    neighbourhood.remove(v)

        # print(str([ x for x in hubs]))
        # print(len(hubs), len(stream.W))
        subs = stream.substream(hubs, hubs)
        # print(subs)
        # print("=========bicore===========/>")
        return subs

    def interior(self, s, X=None, Y=None):
        # print("Calling INTERIOR") 
        core_size = 0
        old_core_size = -1
        hubs = s

        while len(self.find_bicore(hubs).W) != old_core_size:
            # print("IN LOOP")
            hubs = self.find_bicore(hubs)
            old_core_size = len(hubs.W)
        # authorities = self.find_bicore(hubs, threshold=self.a)

        return hubs


    def interior_bak(self, s, X=None, Y=None):
        # Define nodesets
        if X is None and Y is None:
            X = s.V["left"]
            Y = s.V["right"]
        hub = TimeNodeSet()
        authority = TimeNodeSet()
            
        for k, u in enumerate(s.degrees):
            if u in X:
                threshold = self.h
            else:
                threshold = self.a
                
            neigh = set()
            last_times = {} # {u: -1 for u in s.degrees}
            for i in sorted(s.degrees[u], key=itemgetter(1, 2,-3)):
                v, t, ev_type = i[0], i[1], i[2]
                # First check if the property is true
                bha_is_true = len(neigh) >= threshold

                if ev_type == 1:
                    neigh.add(v)
                    last_times[v] = t
                    if not bha_is_true:
                        # While the property is true (typically, we have degree > THRESHOLD)
                        # u remains star, so we should not change the times
                        last_times[u] = t
                else:
                    neigh.remove(v)
                    if bha_is_true:
                        if u in X:
                            hub.add(TimeNode(u, last_times[u], t))
                        else:
                            authority.add(TimeNode(u, last_times[u], t))
        
        return s.substream(hub, authority)
        
class StreamStarSat(StreamProperty):
    
    def __init__(self, stream, threshold=3):
        super().__init__(stream)
        self.threshold = threshold
        
    def interior(self, s):
        """
            Interior function for star satellite, modify to return a stream instead ?
            @param s: a stream graph
            @return: two TimeNodeSets, each containing the k-stars and k-satellites of s
        """
        THRESHOLD = self.threshold
        stars = TimeNodeSet()
        satellites = TimeNodeSet()

        for k, u in enumerate(s.degrees):
            neigh = set()
            best_neighs = set()
            last_times = {} # {u: -1 for u in s.degrees}
            for i in sorted(s.degrees[u], key=itemgetter(1, 2,-3)):
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
        return s.substream(stars, satellites)
    
    def get_values(self):
        return self.stars, self.sat
        
    def p1(self, x): # Star
        # Does (x, b, e) validate the star condition ?
        if self.substream is None or substream != self.substream:
            self.substream = substream
            self.get_stars_sat(u)
        return True, self.stars
        # if self.stars is not None:
        #    return True, self.stars
        
        return True, self.stars
    
    def p2(self, x): # Sat
        if self.substream is None or substream != self.substream:
            self.substream = substream
            self.get_stars_sat(u)
        return True, self.sat
    
    
