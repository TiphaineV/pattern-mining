class TimeNode:
    """
        For later refactoring
    """
    def __init__(self, _node, _b, _e, _label=set()):
        self.node = _node
        self.b = _b
        self.e = _e
        self.label = _label

    @property
    def interval(self):
        return Interval(self.b, self.e)
        
    def __str__(self):
        return f"{self.node} [{self.b}, {self.e}]"

    def __repr__(self):
        return self.__str__()
    
    def __eq__(self, o):
        return  self.node == o.node\
                and self.b == o.b\
                and self.e == o.e
    def __hash__(self):
        return hash((self.node, self.b, self.e))

class Interval:

    def __init__(self, b, e):
        self.b = b
        self.e = e

    def included(self, x):
        """ Returns True is self is included in x,
            False otherwise
        """
        return (x.b <= self.b and self.e <= x.e)

    def intersect(self, x):
        # returns the intersection of two time intervals, or -1 is it is void
        # does not make any asumption obout the order of the intervals, however
        # both i and j *are* intervals (i.e. e >= b, and f >= c)
        # TODO: extend to list of intervals
        # returns both bollean value and intersection (an interval)
        b, e = self.b, self.e
        c, f = x.b, x.e

        # Disjoint
        if c >= e or f <= b:
            return False, None
        # Inclusion
        # Replace to use "included" method
        if (c >= b and f <= e) or \
           (b >= c and e <= f):
                return True, Interval(max(b,c), min(e,f))

        # intersection
        if (c <= b and f >= b and f <= e) or\
           (b <= c and e >= c and e <= f):
            return True, Interval(max(b,c), min(e,f))

        return False, ()


    def union(self, x):
        intersects, inter_val = self.intersect(x)
        if intersects:
            return Interval(min(self.b, x.b), max(self.e, x.e)) 
        else:
            return self, x

    def __str__(self):
        return f"[{self.b}, {self.e}]"

    def __repr__(self):
        return self.__str__()

class TimeNodeSet:

    def __init__(self, elements=[]):
        """
            elements: list of TimeNodes
        """
        self.elements = {}

        for w in elements:
            self.add(w)

    def __iter__(self):
        for u in self.elements.keys():
            for intv, label in self.elements[u]:
                yield TimeNode(u, intv.b, intv.e, label)
                
    def nodes(self):
        return self.elements.keys()
                
    def add(self, x):
        
        if not x.node in self.elements:
            self.elements[x.node] = [ (Interval(x.b, x.e), x.label) ]
            return
        
        for i in range(0, len(self.elements[x.node])):
            intv = self.elements[x.node][i][0]
            b, e = intv.b, intv.e

            if x.interval.included(intv):
                # All elements are already in the set
                return
            intersects, inter_val = x.interval.intersect(intv)
            if intersects:
                self.elements[x.node][i] = (x.interval.union(intv), x.label)
                return
        # New element, add it
        self.elements[x.node].append((x.interval, x.label))
    
    def intersection(self, x):
        """
            Intersection of two TimeNodeSets.
        """
        intersection_set = TimeNodeSet()

        for node in self.elements:
            if node in x.elements:
                # Otherwise cannot be in intersection
                # Merge the two Intervals list (what about labels... ?)
                for i, label in self.elements[node]:
                    for j, label in x.elements[node]:

                        if i.included(j):
                            new_x = TimeNode(node, i.b, i.e, label)
                            intersection_set.add(new_x)
                            continue
                        elif j.included(i):
                            new_x = TimeNode(node, j.b, j.e, label)
                            intersection_set.add(new_x)
                            continue

                        intersects, inter_val = i.intersect(j)
                        if intersects:
                            new_x = TimeNode(node, inter_val.b, inter_val.e, label)
                            intersection_set.add(new_x)
                        # No else, if there is no intersection nor inclusion,
                        # then it's not in the intersection :)
        return intersection_set

    def union(self, x):
        """
            Union of two TimeNodeSets.
        """
        union_set = TimeNodeSet()
        
        keys = set(list(self.elements.keys()) + list(x.elements.keys()))

        for node in keys:
            if node in x.elements:
                cur_set = x
                other_set = self
            else:
                cur_set = self
                other_set = x
            
            if not node in cur_set.elements:
                union_set.elements[node] = other_set.elements[node]
            elif not node in other_set.elements:
                union_set.elements[node] = cur_set.elements[node]
            else:
                for i, label in cur_set.elements[node]:
                    for j, label in other_set.elements[node]:

                        union_val = i.union(j)
                        if type(union_val) is tuple:
                            # Union is disjoint
                            new_x = TimeNode(node, union_val[0].b, union_val[0].e, label)
                            new_x2 = TimeNode(node, union_val[1].b, union_val[1].e, label)
                            union_set.add(new_x)
                            union_set.add(new_x2)
                        else:
                            new_x = TimeNode(node, union_val.b, union_val.e, label)
                            union_set.add(new_x)

                        # No else case, if there is nor intersection nor inclusion,
                        # then it's not in the intersection :)

        return union_set

    def copy(self):
        new = TimeNodeSet()
        new.elements = self.elements.copy()
        return new

    def __len__(self):
        return len(self.values())

    # @property
    def values(self):
        values = []
        for w in self.elements:
            for i in self.elements[w]:
                values.append(TimeNode(w, i[0].b, i[0].e, set()))
        return values
    # Define iter and next properly
    # def __iter__(self):

    
    def __str__(self):
        ret = list(str(self.values()))
        ret = ["{"] + ret[1:-1] + ["}"] 
        return "".join(ret)

    def __repr__(self):
        return str(self.__str__())

if __name__ == '__main__':
    s = TimeNodeSet(elements=[
            TimeNode("u", 2, 4, set()),
            TimeNode("x", 2, 5, set())
        ])

    s2 = TimeNodeSet(elements=[
            TimeNode("x", 2, 3, set()),
            TimeNode("x", 4, 5, set())
        ])
    # x = TimeNode("u", 1, 3, set(["lol"]))
    # x2 = TimeNode("u", 2, 3, set(["lol"]))
    # x3 = TimeNode("u", 2, 5, set(["lol"]))
    # x4 = TimeNode("u", 8, 9, set())
    # s.add(x)
    # s.add(x2)
    # s.add(x3)
