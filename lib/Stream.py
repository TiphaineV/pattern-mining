import sys
import ujson as json
import logging

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

    def p1(self, u, X1, X2, pattern):
        s = self.S
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
            return True, result
        else:
            return False, result
    
    def p2(self, u, X1, X2, pattern):
        s = self.S
        from operator import itemgetter
        result = []

        for x in s.neighbours(u):
            # Find neighbours x of u that are stars
            stars = []
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
                inter_res = s.intersect((b_st, e_st), (b, e))
                
                if not inter_res is None and not inter_res == ():
                    # ie intervals are not disjoint or intersection is void
                    result.append((u, inter_res[0], inter_res[1]))
        
        # pattern = pattern.issubset(s.label(v))
        if len(result) > 0:
            return True, result
        else:
            return False, result

class Stream:
    def __init__(self, lang_left=set(), lang_right=set(), _loglevel=logging.DEBUG):
        self.T = {}
        self.V = []
        self.W = {}
        self.E = {}
        self.core_property = None
        
        # Language
        self.I = (lang_left, lang_right)
        
        # Store both degree view and links (times) view,
        # as the optimal view is different depending on the calculation
        self.degrees = {}
        self.times = {}
        
        self.logger = logging.getLogger()
        self.logger.setLevel(_loglevel)
    
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
                self.times[frozenset([u,v])].append((b, e, label))
            except KeyError:
                self.times[frozenset([u,v])] = [ (b, e, label) ]
    
    def readStream(self, filepath):
        fp = open(filepath)
        data = json.load(fp)
        self.T = data["T"]
        self.V = data["V"]
        self.E = data["E"]
        
        for link in self.E:
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
        # W1: [(u, b,e), (v, b',e'), etc.]
        # returns a substream induced by a subset of W.
        # Only return links etc. involving W1, W2, at their resp. times
        
        subs = Stream()
        subs.T = self.T
        subs.V = set([x[0] for x in  W1 ] + [x[0] for x in W2])
        subs.W = W1 + W2
        subs.E = []
        
        for l in self.E:
            if l["u"] in subs.V and l["v"] in subs.V :
                
                subs.E.append(l)
        
        return subs
    
    def neighbours(self, node):
        return set([ x[0] for x in self.degrees[node] ])
    
    def interior(self, X1, X2,  patterns=(set(), set())):
        stsa = self.core_property
        
        S1 = []
        S2 = []

        while 1:
            old_S1 = S1
            old_S2 = S2
            for u in self.degrees:
                _, tmp = stsa.p1(u, X1, X2, patterns[0])
                __, tmp2 = stsa.p2(u, X1, X2, patterns[1])

                if _ :
                    S1 += tmp
                if __ :
                    S2 += tmp2
            
            if S1 == old_S1 or S2 == old_S2:
                break
                
        return S1, S2

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
    
    def _int(self, left, right):
        """
            Returns the intent of a pattern
            Both left and right are sets (multisets?) for the language
        """
        if left == []:
            left = [set()]
        if right == []:
            right = [set()]
        try:
            return set.intersection(*left), set.intersection(*right)
        except Exception as e:
            print(e)
            print(left)
            print("--------")
            print(right)
            sys.exit()
            
    def _ext(self, left, right):
        """
            Returns the extent (support set) of a pattern
        """
        # Returns support set of a bipattern
        pass
    
    def _minus(self, I, q):
        """
            Returns the candidates for extension
        """
        candidates_left = [(x, 0) for x in set(I[0]).difference(q[0]) ]
        candidates_right = [(x, 1) for x in set(I[1]).difference(q[1]) ]
        
        return set(candidates_left + candidates_right)
    
    def bipatterns(self, _top, _bot):
        """
            Enumerates all bipatterns
        """
        S = self.interior(_top, _bot, (set(), set()))
        self.enum(self._int([self.label(x) for x in S[0]], [self.label(x) for x in S[1]]), S, set())
        
    def _add(self, item, q, side=0):
        _q = (q[0].copy(), q[1].copy())
        if side == 0:
            _q[0].add(item)
        else:
            _q[1].add(item)
        return _q
        
    def enum(self, q, S, EL=set(), depth=0):
        s = 2
        print(q, S, depth)
        #if depth >= 5:
        #   return
#         q = S
        candidates = [x for x in self._minus(self.I, q) if not x in EL]
        self.logger.debug(f'candidats: {candidates}')
        S_bak = (S[0].copy(), S[1].copy())
        for x in candidates:
            # S is not reduced between candidates at the same level of the search tree
            S = (S_bak[0].copy(), S_bak[1].copy())
            # print(f'S: {S}, S_bak: {S_bak}')
            # Extension
            q_x = self._add(x[0], q, side = x[1])
            # self.logger.debug(f'\nConsidering [{x[0]}] q\'={q_x}')
            # Support set of q_x
            S_x = self.interior(S[0], S[1], q_x) # interior(S \cap ext(q))
            #print(f'q_x={q_x} has support set S_x = {S_x}')
            if len(S_x[0].union(S_x[1])) >= s: # Union not sum in case it is not strictly bipartite
                q_x = self._int([ self.label(x) for x in S_x[0] ] , [ self.label(x) for x in S_x[1] ])
                if len(q_x[0].intersection(EL)) == 0 and len(q_x[1].intersection(EL)) == 0:
                    #print(f'Call on {(q_x, S_x, EL)}')
                    self.enum(q_x, S_x, EL, depth+1)
                    EL.add(x)