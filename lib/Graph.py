import networkx as nx
import matplotlib.pyplot as plt
import logging
import copy

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
    def __init__(self, graph, threshold=3):
        super(StarSat, self).__init__(graph)
        self.G = graph
        self.star_degree = threshold * 2 # 2*3 because we are using DiGraphs

    def p1(self, x, Z1, Z2):
        # star : deg >= 3
        subg = self.G.subgraph(Z1.union(Z2))
        deg = subg.degree(x)
        return deg >= self.star_degree

    def p2(self, x, Z1, Z2):
        subg = self.G.subgraph(Z1.union(Z2))
        return any([ subg.degree(i) >= self.star_degree for i in subg.neighbors(x)])
    
class GraphBiPattern:
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

class GraphPattern:
    def __init__(self, _lang=set(), _support_set=set()):
        self.lang = _lang
        self.support_set = _support_set
    
    def elements(self):
        return self.lang
    
    def intent(self):
        labels = [self.support_set.nodes[u]["lang"] for u in self.support_set.nodes() if len(self.support_set.nodes[u]["lang"]) > 0]
        
        if labels == []:
            labels = [set()]
        
        return set.intersection(*labels)
    
    def extent(self, S=None):
        q = self.lang
        
        if S is None:
            S = self.support_set
        else:
            S = S # a graph
            
        return S.subgraph([x for x in S.nodes() if q.issubset(S.nodes[x]["lang"])])
    
    def add(self, x):
        self.lang.add(x)
    
    def minus(self, I):
        return list(set(I).difference(self.lang))
    
    def copy(self):
        return GraphPattern(self.lang.copy(), self.support_set.copy())
    
    def __str__(self):
        return ",".join(self.lang) + ";" + ",".join(map(str, self.support_set.nodes()))
        
class Graph(nx.DiGraph):
    def __init__(self, edges=[(1,2)], lang=set(), _loglevel=logging.WARN):
        super().__init__(edges)
        self.I = lang
        self.logger = logging.getLogger()
        self.logger.setLevel(_loglevel)

    def interior(self, X1, X2):
        prop = StarSat(self, threshold=3)
        
        S1 = X1
        S2 = X2

        Z1 = S1
        Z2 = S2

        while 1:
            Z1 = S1.copy()
            Z2 = S2.copy()

            for x in Z1:
                if not prop.p1(x, Z1, Z2):
                    S1.remove(x)

            for x in Z2:
                if not prop.p2(x, Z1, Z2):
                    S2.remove(x)
            
            if S1 == Z1 or S2 == Z2:
                break 
        # Add attributes to differentiate stars from satellites?
        return self.subgraph(S1.union(S2))


def graph_patterns(graph, s=2):
    G = graph.interior(set(graph.nodes()), set(graph.nodes()).copy())
    p = GraphPattern(set(), G)
    p.lang = p.intent()
    graph_enum(graph, p, s=2, EL=set())
    

def graph_enum(graph, pattern, s=2, EL=set()):
    q = pattern.lang
    
    print(q, graph.nodes())

    candidates = [x for x in pattern.minus(graph.I) if not x in EL]
    
    pattern_bak = pattern.copy()
    for x in candidates:
        # S is not reduced between candidates at the same level of the search tree
        pattern_x = GraphPattern(copy.deepcopy(pattern_bak.lang), pattern_bak.support_set.copy())
        S = pattern_x.support_set

        # Add candidate to pattern
        # print("Adding " + str(x) + " to " + str(pattern_x.lang), str(depth))
        pattern_x.add(x)
        
        # Support set (extent) of q_x
        subs = pattern_x.extent(S=S)

        subs.I = S.I

        # Compute the new interior
        S_x = subs.interior(set(subs.nodes()), set(subs.nodes()).copy())
        p_x = GraphPattern(pattern_x.lang, S_x)
        if len(list(p_x.support_set.nodes())) >= s:
            # Get intent of the new pattern
            p_x.lang = p_x.intent() # S_x.intent([ S_x.label(x) for x in S_x.W.values() ])
            langs = p_x.elements().intersection(EL)
            
            if len(langs) == 0 and p_x.lang != q: #(q_x != q and not (S_x[0] == S[0] and S_x[1] == S[1])):                     
                # print(f"{prefix} Calling enum with {pattern_x.lang}")
                graph_enum(subs, p_x, EL.copy())
                
                # We reached a leaf of the recursion tree, add item to exclusion list
                # print(f"{prefix} Adding {x} to EL")
                # glob_stream.EL.add(x)
                EL.add(x)