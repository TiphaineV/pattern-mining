import networkx as nx
import matplotlib.pyplot as plt
import logging

class Property():
    def __init__(self, graph):
        self.G = graph
        
    def p1(self):
        return True

    def p2(self):
        return True

class BHACore(Property):
    def __init__(self, graph):
        super(BHACore, self).__init__(graph)
        self.h = 2
        self.a = 2
        
    def p1(self, x, Z1, Z2, pattern):
        subg = self.G.subgraph(Z1.union(Z2))
        degree = subg.out_degree(x)
        pattern = pattern.issubset(self.G.nodes[x]["lang"])
        
        return degree >= self.h and pattern
        
    def p2(self, x, Z1, Z2, pattern):
        subg = self.G.subgraph(Z1.union(Z2))
        degree = subg.in_degree(x)
        pattern = pattern.issubset(self.G.nodes[x]["lang"])
        
        return degree >= self.a and pattern

class StarSat(Property):
    def __init__(self, graph):
        super(StarSat, self).__init__(graph)
        self.G = graph
        self.star_degree = 3  # 2*3 because we are using DiGraphs

    def p1(self, x, Z1, Z2, pattern):
        # star : deg > 3
        subg = self.G.subgraph(Z1.union(Z2))
        deg = subg.degree(x)
        pattern = pattern.issubset(self.G.nodes[x]["lang"])
        
        return deg >= self.star_degree and pattern

    def p2(self, x, Z1, Z2, pattern):
        subg = self.G.subgraph(Z1.union(Z2))
        pattern = pattern.issubset(self.G.nodes[x]["lang"])
        
        return any([ subg.degree(i) >= self.star_degree for i in subg.neighbors(x)]) and pattern
    
class BiPattern:
    # TODO: Refactoring
    def __init__(self):
        self.left_pattern = set()
        self.right_pattern = set()
        self.left_support = set()
        self.right_support = set()
        
    def intent(self):
        # Returns the intent of the pattern
        return self.left_pattern, self.right_pattern
    
    def extent(self):
        # Returns the extent of the pattern
        return self.left_support, self.right_support
    
    def add(self, x, side):
        if side == 0:
            self.left_pattern.add(x)
        else:
            self.right_pattern.add(x)
    

class Graph(nx.DiGraph):
    def __init__(self, edges=[(1,2)], lang_left=set(), lang_right=set(), _loglevel=logging.WARN):
        super().__init__(edges)
        self.I = (lang_left, lang_right)
        self.logger = logging.getLogger()
        self.logger.setLevel(_loglevel)

    def interior(self, X1, X2, patterns=(set(), set())):
        prop = BHACore(self)
        
        S1 = X1
        S2 = X2

        Z1 = S1
        Z2 = S2

        while 1:
            Z1 = S1.copy()
            Z2 = S2.copy()

            for x in Z1:
                if not prop.p1(x, Z1, Z2, patterns[0]):
                    S1.remove(x)

            for x in Z2:
                if not prop.p2(x, Z1, Z2, patterns[1]):
                    S2.remove(x)
            
            if S1 == Z1 or S2 == Z2:
                break 

        return S1, S2

    def _int(self, left, right):
        """
            Both left and right are sets (multisets?) for the language
        """
#         print(f"_int: {type(left)} {left}, {type(right)} {right}")
        if left == []:
            left = [set()]
        if right == []:
            right = [set()]
        return set.intersection(*left), set.intersection(*right)
    
    def _ext(self, left, right):
        # Returns support set of a bipattern
        pass
    
    def _minus(self, I, q):
        
        candidates_left = [(x, 0) for x in I[0].difference(q[0]) ]
        candidates_right = [(x, 1) for x in I[1].difference(q[1]) ]
        
        return set(candidates_left + candidates_right)
    
    def bipatterns(self, _top, _bot):
        S = self.interior(_top, _bot, (set(), set()))
        self.enum(self._int([self.nodes[x]["lang"] for x in S[0]], [self.nodes[x]["lang"] for x in S[1]]), S, set())
        
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
            self.logger.debug(f'\nConsidering [{x[0]}] q\'={q_x}')
            # Support set of q_x
            S_x = self.interior(S[0], S[1], q_x) # interior(S \cap ext(q))
            #print(f'q_x={q_x} has support set S_x = {S_x}')
            if len(S_x[0].union(S_x[1])) >= s: # Union not sum in case it is not strictly bipartite
                q_x = self._int([ self.nodes[x]["lang"] for x in S_x[0] ] , [ self.nodes[x]["lang"] for x in S_x[1] ])
                if len(q_x[0].intersection(EL)) == 0 and len(q_x[1].intersection(EL)) == 0:
                    #print(f'Call on {(q_x, S_x, EL)}')
                    self.enum(q_x, S_x, EL, depth+1)
                    EL.add(x)

