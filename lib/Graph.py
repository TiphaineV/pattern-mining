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
    def __init__(self, graph, h=2, a=2):
        super().__init__(graph)
        self.h = h
        self.a = a
        
    def p1(self, x, Z1, Z2):
        subg = self.G.subgraph(Z1.union(Z2))
        degree = subg.out_degree(x)
        
        return degree >= self.h
        
    def p2(self, x, Z1, Z2):
        subg = self.G.subgraph(Z1.union(Z2))
        degree = subg.in_degree(x)
        
        return degree >= self.a

class StarSat(Property):
    def __init__(self, graph, threshold=3):
        super().__init__(graph)
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
    def __init__(self, lang=(set(), set()), support_set=set()):
        self.lang = lang
        self.support_set = support_set
    
    def elements(self):
        return set(list(self.lang[0]) + list(self.lang[1]))
    
    def intent(self):
        # Returns the intent of the pattern
        labels = [self.support_set.nodes[u] for u in self.support_set.nodes() if len(self.support_set.nodes[u]["lang"]) > 0]
        # print(self.support_set.nodes())
        # print(labels)
        top_labels = [ x["lang"] for x in labels if x["bipartite"] == 0 ]
        bot_labels = [ x["lang"] for x in labels if x["bipartite"] == 1 ]
        if top_labels == []:
            top_labels = [set()]
        if bot_labels == []:
            bot_labels = [set()]
        
        return set.intersection(*top_labels), set.intersection(*bot_labels)
    
    def extent(self, S=None):
        q, r = self.lang[0], self.lang[1]
        
        if S is None:
            S = self.support_set
        else:
            S = S # a graph
        
        return S.subgraph([x for x in S.nodes() if q.issubset(S.nodes[x]["lang"]) or r.issubset(S.nodes[x]["lang"])])
    
    def minus(self, I):
        top_candidates = [ (x, 0) for x in set(I[0]).difference(self.lang[0]) ]
        bot_candidates = [ (x, 1) for x in set(I[1]).difference(self.lang[1]) ]
        
        return top_candidates, bot_candidates
    
    def add(self, x, side):
        if side == 0:
            self.lang[0].add(x)
        else:
            self.lang[1].add(x)
            
    def copy(self):
        return GraphBiPattern((self.lang[0].copy(), self.lang[1].copy()), self.support_set.copy())
    
    def __str__(self):
        return ",".join(self.lang) + ";" + ",".join(map(str, self.support_set.nodes()))
        
    def json(self):
        return { "lang": {"left": list(self.lang[0]), "right": list(self.lang[1])}, "support_set": list(self.support_set.nodes()) }

    @staticmethod
    def from_json(obj):
        p = GraphBiPattern()
        p.lang = obj["lang"]
        p.support_set = obj["support_set"] 

        return p

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
        
    def json(self):
        return { "lang": list(self.lang), "support_set": list(self.support_set.nodes()) }

    @staticmethod
    def from_json(obj):
        p = GraphPattern()
        p.lang = obj["lang"]
        p.support_set = obj["support_set"] 

        return p


class Graph(nx.DiGraph):
    def __init__(self, edges=[], lang=set(), _loglevel=logging.WARN):
        super().__init__(edges)
        self.I = lang
        self.logger = logging.getLogger()
        self.logger.setLevel(_loglevel)
        self.pattern_list = []

    def interior(self, X1, X2, prop=None):
        if prop is None:
            prop = StarSat(self, threshold=2)
        
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

    
class BipartiteGraph(Graph):
    def __init__(self, edges=[], lang=(set(), set()), nodes=(set(), set()), _loglevel=logging.WARN):
        super().__init__(edges)
        self.I = lang # I[0] and I[1]
        self.top = set()
        self.bot = set()

    def interior(self, X1, X2, prop=None):
        if prop == None:
            prop = StarSat(self, threshold=2)
        
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
    graph.pattern_list = []
    G = graph.interior(set(graph.nodes()), set(graph.nodes()).copy())
    p = GraphPattern(set(), G)
    p.lang = p.intent()
    graph_enum(graph, p, s=2, EL=set(), graph_obj=graph)
    

def graph_enum(graph, pattern, s=2, EL=set(), graph_obj=None):
    q = pattern.lang
    
    print(q, graph.nodes())
    graph_obj.pattern_list.append(pattern)

    candidates = [x for x in pattern.minus(graph.I) if not x in EL]
    
    pattern_bak = pattern.copy()
    for x in candidates:
        # S is not reduced between candidates at the same level of the search tree
        pattern_x = GraphPattern(copy.deepcopy(pattern_bak.lang), pattern_bak.support_set.copy())
        S = pattern_x.support_set.copy()

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
                graph_enum(subs, p_x, EL.copy(), graph_obj=graph)
                
                # We reached a leaf of the recursion tree, add item to exclusion list
                # print(f"{prefix} Adding {x} to EL")
                EL.add(x)
                

def bigraph_patterns(graph, s=2, prop=None):
    graph.pattern_list = []
    top = [ x for x in graph.nodes() if graph.nodes[x]["bipartite"] == 0 ]
    bot = [ x for x in graph.nodes() if graph.nodes[x]["bipartite"] == 1 ]
    G = graph.interior(set(top), set(bot), prop=prop)
    p = GraphBiPattern((set(), set()), G)
    p.lang = p.intent()
    bigraph_enum(graph, p, s=2, EL=set(), graph_obj=graph, prop=prop)
    

def bigraph_enum(graph, pattern, s=2, EL=set(), graph_obj=None, prop=None):
    q = pattern.lang
    
    print(q, graph.nodes())
    graph_obj.pattern_list.append(pattern)

    candidates = pattern.minus(graph.I) # return side as well
    candidates = candidates[0] + candidates[1]
    candidates = [ x for x in candidates if x[0] not in EL ]
    # print(candidates)
    pattern_bak = pattern.copy()
    for x, side in candidates:
        # S is not reduced between candidates at the same level of the search tree
        pattern_x = GraphBiPattern(copy.deepcopy(pattern_bak.lang), pattern_bak.support_set.copy())
        S = pattern_x.support_set.copy()

        # Add candidate to pattern
        
        # print("Adding " + str(x) + " to " + str(pattern_x.lang[side]))
        pattern_x.add(x, side=side)
        
        # Support set (extent) of q_x
        subs = pattern_x.extent(S=S)

        subs.I = S.I

        # Compute the new interior
        S_x = subs.interior(set(subs.nodes()), set(subs.nodes()).copy(), prop=prop)
        p_x = GraphBiPattern(pattern_x.lang, S_x)
        if len(list(p_x.support_set.nodes())) >= s:
            # Get intent of the new pattern
            p_x.lang = p_x.intent() # S_x.intent([ S_x.label(x) for x in S_x.W.values() ])
            langs = p_x.elements().intersection(EL)
            
            if len(langs) == 0 and p_x.lang != q: #(q_x != q and not (S_x[0] == S[0] and S_x[1] == S[1])):                     
                # print(f"Calling enum with {pattern_x.lang}")
                bigraph_enum(subs, p_x, EL.copy(), graph_obj=graph)
                
                # We reached a leaf of the recursion tree, add item to exclusion list
                # print(f"{prefix} Adding {x} to EL")
                EL.add(x)