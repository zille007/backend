from DataStructures import PriorityQueue


SEARCH_DEBUG = False


class Search(object):
    """
    Generic interface for search algorithms.

    neighbors is a function that takes a single node and returns a list containing its neighbors
    """
    def __init__(self, neighbors):
        self.neighbors = neighbors

    def search(self, start, end, data=None):
        return []


class AStar1(Search):
    """
    A* pathfinder algorithm from existing TATD-source, slightly refitted.
    It now inherits from Search, and takes g- and h-functions as parameters, as well as the neighbors-function.
    """
    def __init__(self, neighbors, g, h):
        super(AStar1, self).__init__(neighbors)
        self.g = g
        self.h = h

    def search(self, start, end, data=None):
        if start is None or end is None:
            return []
        openset = set()
        closedset = set()
        current = start
        openset.add(current)
        parents = {}
        gs = {start: 0}
        hs = {start: self.h(start, end, data)}
        fs = {start: gs[start] + hs[start]}
        iters = 0
        c = 0
        o = 1
        while openset:
            iters += 1
            if iters > 100000:
                print "Pathfinder in infinite loop???"
                return None

            current = min(openset, key=lambda o:gs[o] + hs[o])

            if current is end:
                if SEARCH_DEBUG:
                    print "AStar1:"
                    print "c: " + str(c)
                    print "o: " + str(o)
                return recons_path(parents, end)

            c += 1
            openset.remove(current)
            closedset.add(current)
            for node in self.neighbors(current):
                if node in closedset:
                    continue
                if node in openset:
                    o += 1
                    new_g = gs[current] + self.g(current, node, data)
                    if gs[node] > new_g:
                        gs[node] = new_g
                        parents[node] = current
                else:
                    o += 1
                    gs[node] = gs[current] + self.g(current, node, data)
                    hs[node] = self.h(node, end, data)
                    fs[node] = gs[node] + hs[node]
                    parents[node] = current
                    openset.add(node)
        return None


class AStar2(Search):
    """
    Another A* implementation. Wikipedia pseudocode used as template:
    http://en.wikipedia.org/wiki/A*_search_algorithm
    """
    def __init__(self, neighbors, g, h):
        super(AStar2, self).__init__(neighbors)
        self.g = g
        self.h = h

    def search(self, start, end, data=None):
        if start is None or end is None:
            return []

        openQueue = PriorityQueue()
        closedSet = set()
        parents = dict()

        gs_start = 0
        gs = {start: gs_start}
        fs_start = gs_start + self.h(start, end, data)
        fs = {start: fs_start}

        openQueue.add(fs_start, start)

        c = 0
        o = 1
        while openQueue.count() > 0:
            current = openQueue.pop()

            if current is end:
                if SEARCH_DEBUG:
                    print "AStar2:"
                    print "c: " + str(c)
                    print "o: " + str(o)
                return recons_path(parents, end)

            c += 1
            closedSet.add(current)
            for n in self.neighbors(current):
                gn = gs[current] + self.g(current, n, data)
                if n in closedSet:
                    if gn >= gs[n]:
                        continue

                inOpen = openQueue.contains(n)
                if not inOpen or (gn < gs[n]):
                    o += 1
                    parents[n] = current
                    gs[n] = gn
                    fn = gn + self.h(n, end, data)
                    fs[n] = fn
                    if not inOpen:
                        openQueue.add(fn, n)

        return None


class AStar3(Search):
    """
    Yet another A* implementation. Amit Patel's pseudocode used as template:
    http://theory.stanford.edu/~amitp/GameProgramming/
    """
    def __init__(self, neighbors, g, h):
        super(AStar3, self).__init__(neighbors)
        self.g = g
        self.h = h

    def search(self, start, end, data=None):
        if start is None or end is None:
            return []

        openQueue = PriorityQueue()
        closedSet = set()
        parents = dict()

        gs_start = 0
        gs = {start: gs_start}
        fs_start = gs_start + self.h(start, end, data)
        fs = {start: fs_start}

        openQueue.add(fs_start, start)

        c = 0
        o = 1
        while openQueue.count() > 0:
            current = openQueue.pop()

            if current is end:
                if SEARCH_DEBUG:
                    print "AStar3:"
                    print "c: " + str(c)
                    print "o: " + str(o)
                return recons_path(parents, end)

            c += 1
            closedSet.add(current)

            for n in self.neighbors(current):
                gn = gs[current] + self.g(current, n, data)

                if openQueue.contains(n) and gn < gs[n]:
                    openQueue.remove(n)

                if n in closedSet and gn < gs[n]:
                    closedSet.remove(n)

                if not openQueue.contains(n) and n not in closedSet:
                    o += 1
                    gs[n] = gn
                    fn = gn + self.h(n, end, data)
                    fs[n] = fn
                    openQueue.add(fn, n)
                    parents[n] = current


def recons_path(parents, current):
    if current in parents:
        return recons_path(parents, parents[current]) + [current]
    else:
        return [current]