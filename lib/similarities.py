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

def bipattern_similarity(s, p, q):
    """
        s: the stream graph on which the patterns are enumerated
        p,q: two Patterns or BiPatterns
        @return: the similarity between two patterns.
    """
    
    top, bot = s.V["left"], s.V["right"]
    
    get_w = lambda p: (TimeNodeSet([x for x in p.support_set.W if x.node in top]), TimeNodeSet([x for x in p.support_set.W if x.node in bot]))
    
    W1 = get_w(p)
    W2 = get_w(q)
    
    score_top = len(W1[0].intersection(W2[0])) / len(W1[0].union(W2[0]))
    score_bot = len(W1[1].intersection(W2[1])) / len(W1[1].union(W2[1]))
    
    return 1 - min(score_top, score_bot)