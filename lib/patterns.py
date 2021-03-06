from lib.TimeNode import TimeNode, TimeNodeSet
from lib.Stream import *
from lib.StreamProperties import *
import operator
from lib.errors import *
import copy
import ujson as json
import sys
from operator import itemgetter

import networkx as nx

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
        
        langs = [ self.support_set.label(x) for x in self.support_set.W.values() if len(self.support_set.label(x)) > 0 ]

        if langs == []:
            langs = [set()]
        return set.intersection(*langs)

    def extent(self, S=None):
        """
            Returns the extent (support set) of a pattern in a stream S
        """
        q = self.lang
        
        # if S is None:
            # S = (self.support_set.E, self.support_set.E)
        # else:
            # S = (S.E, S.E)
            
        X1 = [ TimeNode(x["u"], x["b"], x["e"], _label=set(x["label"]["left"])) for x in S.E if q.issubset(set(x["label"]["left"]))]
        X2 = [ TimeNode(x["v"], x["b"], x["e"], _label=set(x["label"]["right"])) for x in S.E if q.issubset(set(x["label"]["right"]))]
        
        X = X1 + X2
        X = TimeNodeSet(X)

        return X
    
    def elements(self):
        return self.lang
    
    def copy(self):
        return Pattern(self.lang.copy(), self.support_set.copy())
    

    @staticmethod
    def from_json(obj):
        p = Pattern()
        q = set(obj["lang"])
        support_set = Stream()
        support_set.loadJson(obj["support_set"])

        p.lang = q
        p.support_set = support_set 

        return p


    def json(self):
        json_repr = {
            "lang": list(self.lang),
            "support_set": self.support_set.json()
        }

        return json_repr

    def __str__(self):
        return f"{self.lang} {[str(x) for x in self.support_set.W]}"
        
    def __repr__(self):
        return self.__str__()
    
    def __eq__(self, o):
        return self.lang == o.lang and self.support_set == o.support_set
        
class BiPattern:
    """
        Bipattern class
    """
    def __init__(self, _lang={ "left": [], "right": [] }, _support_set=set()):
        self.lang = _lang
        self.support_set = _support_set
    
    def json(self):
        json_repr = {
            "lang": { "left": list(self.lang["left"]), "right": list(self.lang["right"]) },
            "support_set": self.support_set.json()
        }

        return json_repr
    
    def add(self, item, side):
        if side == 0:
            self.lang["left"].add(item)
        else:
            self.lang["right"].add(item)
        
    def minus(self, I):
        assert(len(self.lang["left"]) <= len(I["left"]))
        assert(len(self.lang["right"]) <= len(I["right"]))
        return set([ x for x in set(I["left"]).difference(self.lang["left"]) ]), set([ x for x in set(I["right"]).difference(self.lang["right"]) ])
    
    def elements(self):
        return self.lang["left"].union(self.lang["right"])
    
    def intent(self):
        """
            Returns the intent of a pattern
        """
        
        langs_left = [ self.support_set.label(x) for x in self.support_set.W.values() if x.node in self.support_set.V["left"] ]
        langs_right = [ self.support_set.label(x) for x in self.support_set.W.values() if x.node in self.support_set.V["right"] ]
        
        if langs_left == []:
            langs_left = [set()]
        if langs_right == []:
            langs_right = [set()]

        return { "left": set.intersection(*langs_left), "right": set.intersection(*langs_right) }

    def extent(self, S=None):
        """
            Returns the extent (support set) of a pattern in a stream S
        """
        q = self.lang
        
        # for x in S.E:
            # if len(q["left"]) > 0 and len(x["label"]["left"]) > 0:
                # assert(list(q["left"])[0][0] == list(x["label"]["left"])[0][0])
            # if len(q["right"]) > 0 and len(x["label"]["right"]) > 0:
                # assert(list(q["right"])[0][0] == list(x["label"]["right"])[0][0])

        X1 = [ TimeNode(x["u"], x["b"], x["e"]) for x in S.E if q["left"].issubset(set(x["label"]["left"]))]
        X2 = [ TimeNode(x["v"], x["b"], x["e"]) for x in S.E if q["right"].issubset(set(x["label"]["right"]))]
        
        X = X1 + X2
        X = TimeNodeSet(X)

        return X
    
    def copy(self):
        """
            Returns a copy of the current BiPattern object.
        """
        return BiPattern(copy.deepcopy(self.lang), self.support_set.copy())
    
    def __str__(self):
        lang_left = "|".join(map(str, self.lang['left']))
        lang_right = "|".join(map(str, self.lang['right']))
        return f"{lang_left}, {lang_right} {str(list(self.support_set.W))}"
        
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
    return prop.interior(s)

def check_patterns(pattern_list):
    """
        Perform some basic sanity checks on a (bi)pattern list,
        to ensure its validity.
    """
    # Ensure all patterns enumerated are unique
    num_patterns = len(pattern_list)
    unique_patterns = len([ frozenset(p[0].lang) for p in pattern_list ])
    unicity = (num_patterns == unique_patterns)
    
    # Ensure all patterns are more specific than their parent
    specificity = all([ len(p[0].lang) >= len(p[1]) for p in pattern_list ])

    return unicity and specificity

def check_bha_patterns(stream):
    check_res = []
    for i in stream.pattern_list:
         edges = [frozenset([ x["u"], x["v"] ]) for x in i[0].support_set.E ]
         g = nx.Graph(edges)
         deg = [ g.degree(x) >= stream.core_property.h for x in g.nodes() ]
         check_res.append(all(deg))
    return all(check_res)
    
def load_patterns(filepath, bipartite=False, bipatterns=False):
    """
        Load patterns from a previous run, that have been exported in JSON format,
        using Pattern's self.json() method.
    """
    
    if bipartite:
        streamClass = BipartiteStream
    else:
        streamClass = Stream

    if bipatterns:
        patternClass = BiPattern
    else:
        patternClass = Pattern
    print(streamClass)

    patterns_list = []
    res_file = open(filepath)
    for line in res_file:
        line = line.replace("'", "\"")
        data = json.loads(line.strip())
        tmp_stream = streamClass()
        tmp_stream.loadJson(data["support_set"])
        p = patternClass(data["lang"], tmp_stream)
        patterns_list.append(p)

    return patterns_list

def bipatterns(stream, s=2):
    """
        Enumerates all bipatterns
    """

    # Check that stream can enumerate monopatterns
    if not stream.bipatterns_flag:
        raise ValueError("The stream is not formatted for bipattern enumeration. Make sure that the language description (stream.I) is a dictionary containing lists, likes so: {'left': ..., 'right':...}.")
        sys.exit()

    stream.EL = set()
    stream.pattern_list = []
    # S = interior(self, _top, _bot, set())
    S = stream.core_property.interior(stream)
#     pattern = Pattern(set(), S)
    pattern = BiPattern({ "left": set(), "right": set() }, S)
    pattern.lang = pattern.intent() # Pattern(stream.intent([stream.label(x) for x in stream.W.values()]),S)
    enum(stream, pattern, set(), min_support_size=s, glob_stream=stream, patternClass=BiPattern)
    
    return stream.pattern_list

def patterns(stream, s=2):  
    """
        Enumerates all patterns
    """

    # Check that stream can enumerate monopatterns
    if not stream.patterns_flag:
        raise ValueError("The stream is not formatted for pattern enumeration. Make sure that the language description (stream.I) is a single list.")
        sys.exit()

    stream.EL = set()
    excl_list = set()
    stream.pattern_list = []
    # S = interior(self, _top, _bot, set())
    S = stream.core_property.interior(stream)
    pattern = Pattern(set(), S)
    pattern.lang = pattern.intent() # Pattern(stream.intent([stream.label(x) for x in stream.W.values()]),S)
    enum(stream, pattern, set(), min_support_size=s, glob_stream=stream, patternClass=Pattern)

    return stream.pattern_list
    

DEPTH_STREAM = {}

def enum(stream, pattern, excl_list=set(), depth=0, min_support_size=2, parent=set(), glob_stream=None, patternClass=None):
    """
        Internal routine for pattern enumeration.
        Should not be called outside of patterns/bipatterns ?
    """
    
    # patternClass = BiPattern
    
    # Pretty print purposes
    prefix = depth * 4 * ' '
    
    q = pattern.lang
    S = pattern.support_set
    
    glob_stream.pattern_list.append((pattern, parent))

    # json.dump(pattern.json(), glob_stream.bip_fp)
    print(pattern, file=glob_stream.bip_fp)
    # ipdb.set_trace()
    # print(",", file=glob_stream.bip_fp)

    
    # Let us restrict the set of candidates. While it is at most I,
    # however, elements of I that do not appear in the support set S of the pattern cannot be potential
    # candidates. 
    # lang = [ S.label(x) for x in S.W.values() ]
    # lang = [item for sublist in lang for item in list(sublist) if item not in pattern.elements() ]
    # candidates = set(lang)
    # lang = stream.I
    if patternClass is BiPattern:
        top_cand, bot_cand = pattern.minus(stream.I)
        candidates = [ (x, 0) for x in top_cand if not x in excl_list ] + [ (x, 1) for x in bot_cand if not x in excl_list ]
    else:
        candidates = pattern.minus(stream.I)
        candidates = [ (x, 0) for x in candidates if not x in excl_list ]
    
    sort_crit = lambda x: len(x)
    # candidates = [ (x, 0) for x in top_cand if not x in excl_list ] + [ (x, 1) for x in bot_cand if not x in excl_list ]

    # print(len(pattern.lang), len(pattern.support_set.W), len(pattern.support_set.V), len(pattern.support_set.E))
    # print(len(candidates), depth)
    
    # bak variables are necessary so that deeper recursion levels do not modify the current object
    pattern_bak = pattern.copy()
    # for x, side in sorted(candidates, key=sort_crit(itemgetter(0))):
    for x, side in candidates:
        # S is not reduced between candidates at the same level of the search tree
        pattern_x = patternClass(copy.deepcopy(pattern_bak.lang), pattern_bak.support_set.copy())
        supp_set = pattern_x.support_set

        # Add candidate to pattern
        # print("Adding " + str(x) + " to " + str(pattern_x.lang), str(depth))
        if patternClass is BiPattern:
            pattern_x.add(x, side)
        else:
            # (mono)Pattern case
            pattern_x.add(x)
        
        # Support set (extent) of q_x
        # print(f"Getting extent of {pattern_x.lang}")
        X = pattern_x.extent(S=stream)
        # print(f"{pattern_x.lang} has extent {list(X)}")
        S_x = (X.intersection(stream.W).copy(), X.intersection(stream.W).copy())

        # print(f"Getting intersected substream of {pattern_x.lang}")
        subs = stream.substream(S_x[0], S_x[1])
        # print(f"subs size is {len(subs.W)}")
        # subs.I = copy.deepcopy(S.I) # already set in substream()
        subs.setCoreProperty(stream.core_property)
        subs.EL = copy.deepcopy(glob_stream.EL)

        # Compute the new interior
        # print(f"Getting interior of {pattern_x.lang}")
        S_x = subs.core_property.interior(subs)
        # print(S_x.I)
        # print(f"s_x size is {len(S_x.W)}")
        
        p_x = patternClass(copy.deepcopy(pattern_x.lang), S_x.copy())

        if len(list(p_x.support_set.W)) >= min_support_size:
            # Get intent of the new pattern
            # print(f"added lang: {p_x.lang}")
            p_x.lang = p_x.intent() # S_x.intent([ S_x.label(x) for x in S_x.W.values() ])
            # print(f"new lang: {p_x.lang}")
            langs = p_x.elements().intersection(excl_list)
            
            if len(langs) == 0 and p_x.lang != q: #(q_x != q and not (S_x[0] == S[0] and S_x[1] == S[1])):                     
                # print(f"{prefix} Calling enum with {pattern_x.lang}")
                enum(subs, p_x, copy.deepcopy(excl_list), depth+1, parent=q, glob_stream=glob_stream, patternClass=patternClass)
                
                # We reached a leaf of the recursion tree, add item to exclusion list
                # print(f"{prefix} Adding {x} to EL")
                # glob_stream.EL.add(x)
                excl_list.add(x)

def fp_close(self):
    self.bip_fp.close()
