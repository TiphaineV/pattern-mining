from lib.Stream import Stream
from lib.TimeNode import TimeNode, TimeNodeSet


def jaccard(s, u, v):
    """
        s: a Stream object
        u,v : two nodes

        @return: the Jaccard coefficient of u and v
    """

    n_u = TimeNodeSet([TimeNode(x, b, e) for x in s.neighbours(u) for b,e,l_u,l_v in s.times[frozenset([u, x])] ])
    n_v = TimeNodeSet([TimeNode(x, b, e) for x in s.neighbours(v) for b,e,l_u,l_v in s.times[frozenset([v, x])] ])

    # Union
    union = sum(( x.e - x.b for x in n_u.union(n_v) ))

    # Intersection
    inter = sum( ( x.e - x.b for x in n_u.intersection(n_v) ) )

    return inter / union

def bipattern_distance(s, p, q):
    """
        s: the stream graph on which the patterns are enumerated
        p,q: two BiPatterns
        @return: the similarity between two patterns.
    """
    
    
    top, bot = s.V["left"], s.V["right"]
    get_w = lambda p: (TimeNodeSet([x for x in p.support_set.W if x.node in top]), TimeNodeSet([x for x in p.support_set.W if x.node in bot]))
    
    W1 = get_w(p)
    W2 = get_w(q)
    
    score_top = len(W1[0].intersection(W2[0])) / len(W1[0].union(W2[0]))
    score_bot = len(W1[1].intersection(W2[1])) / len(W1[1].union(W2[1]))
    
    return 1 - min(score_top, score_bot)

def pattern_distance(s, p, q):
    """
        s: the stream graph on which the patterns are enumerated
        p,q: two Patterns
        @return: the similarity between two patterns.
    """
    
    nodeset = s.V
    get_w = lambda p: TimeNodeSet([x for x in p.support_set.W if x.node in nodeset])
    
    W1 = get_w(p)
    W2 = get_w(q)
        
    score = len(W1.intersection(W2)) / len(W1.union(W2))
    
    return 1 - score

def _is_close( p, s, stream_g, beta) :
    """
        Returns True if the pattern p is at a distance less than
        beta from at least one pattern in the s list, and False
        otherwise.
    """
    
    if not "Bipartite" in str(type(stream_g)):
        distance_func = pattern_distance
    else:
        distance_func = bipattern_distance
    
    i = 0
    while( len(s) > i and distance_func(stream_g, p, s[i]) > beta ) :
        i+= 1
    return (i < len(s))

def _find_first_distant_patt_pos( f, s, stream_g, beta ) :
    """
        Returns the position in the list of candidate patterns f of
        the first pattern which is at a distance greater than beta
        from all the patterns already selected in s
    """
    i = 0
    while( len(f) > i and _is_close( f[i], s, stream_g, beta)):
        i += 1
    return(i)

def g_beta_selection( p_list, stream_g, beta) :
    """
        Selects from the ordered list of patterns p a sub-list in
        which each any pairs of selected patterns are at a distance
        greater than beta.
    
        p_list : ordered list of patterns
        stream_g: the stream graph on which the patterns are enumerated
        dist_func : function such that dist_func( p[i], p[j])
            returns a distance for any i,j < len(p) - ie for any
            pair of patterns taken from p.
        beta : distance threshold
        
        @return: a selection of patterns, subset of p_list
    """
    f = p_list.copy() # copy of the list of ordered patterns on which the selection is done
    s = [] # list of selected patterns
    while( 0 < len(f)):
        # position in the list of candidate patterns of
        # the first pattern which is at a distance greater
        # than beta from all the patterns already selected
        pos_next = _find_first_distant_patt_pos( f, s, stream_g, beta )
        # 
        if( pos_next < len(f) ):
            s.append(f[pos_next]) # Adds the found pattern to the selected patterns list s.
        f = f[ pos_next + 1 : ] # Removes from the candidate list f all previous patterns that
                                # are close to at least one of the patterns already selected
    return s
