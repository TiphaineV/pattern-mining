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
