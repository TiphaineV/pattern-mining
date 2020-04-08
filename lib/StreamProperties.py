from lib.TimeNode import Interval

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
    # Modify to check if (u, [b,e]) respects k-Star/k-Sat, returns True + an interval included in [b,e] or False, []
    
    def __init__(self, stream, threshold=3):
        super().__init__(stream)
        self.star_degree = threshold

    def p1(self, u, substream):
        s = substream # self.S.substream(X1, X2)
        from operator import itemgetter
        result = []
        times = s.degrees[u]
        sorted_times = sorted(times, key=itemgetter(1))

        prop_true_t = 0
        deg = 0
        prop_was_true = False

        for v, t, ev_type, label in sorted_times:
            prop_is_true = False
            if ev_type == 1:
                deg += 1
            elif ev_type == -1:
                deg -= 1

            if deg >= self.star_degree:
                if not prop_was_true:
                    prop_true_t = t
                prop_is_true = True
                prop_was_true = True

            if not prop_is_true and prop_was_true:
                result.append((u, prop_true_t, t))
                prop_was_true = False

        # pattern = pattern.issubset(s.label(u))
        
        if len(result) > 0:
            return True, set(result)
        else:
            return False, set(result)
    
    def p2(self, u, substream):
        # First extract the substream induced by X1 and X2
        s = substream # self.S.substream(X1, X2)
        # s = self.S
        from operator import itemgetter
        result = []
        stars = []

        for x in s.neighbours(u):
            # Find neighbours x of u that are stars
            # stars = []
            times = s.degrees[x]
            sorted_times = sorted(times, key=itemgetter(1))

            prop_true_t = 0
            deg = 0
            prop_was_true = False

            for v, t, ev_type, label in sorted_times:
                # Determine when x is star
                prop_is_true = False
                if ev_type == 1:
                    deg += 1
                elif ev_type == -1:
                    deg -= 1

                if deg >= self.star_degree:
                    if not prop_was_true:
                        prop_true_t = t
                    prop_is_true = True
                    prop_was_true = True

                if not prop_is_true and prop_was_true:
                    stars.append((x, prop_true_t, t))
                    
                    prop_was_true = False
        
        for v, b_st, e_st in stars:
            times = s.times[frozenset([u, v])]
            for x in times:
                b, e = x[0], x[1]
                intv = Interval(b,e)
                intv_st = Interval(b_st, e_st)
                inter_res, inter_val = intv.intersect(intv_st)
                
                if inter_res:
                    # ie intervals are not disjoint or intersection is void
                    result.append((u, inter_val.b, inter_val.e))
        
        if len(result) > 0:
            return True, set(result)
        else:
            return False, set(result)
