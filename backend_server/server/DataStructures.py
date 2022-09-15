class PriorityQueue(object):
    """
    Couldn't find a useful PriorityQueue implementation on the web.
    Can you believe it?!

    No I can't, because I actually read documentation and thus know about Queue.PriorityQueue().

    So I made my own. Here's an ode to all PQs in the world:
    """
    __slots__ = ["queue"]

    def __init__(self):
        self.queue = []

    def add(self, priority, element):
        if len(self.queue) is 0:
            self.queue.append((priority, element))
            return

        if priority < self.queue[-1][0]:
            self.queue.append((priority, element))
            return

        index = -1
        for i in xrange(len(self.queue)):
            if priority > self.queue[i][0]:
                index = i
                break
        if index < 0:
            self.queue.append((priority, element))
        else:
            self.queue.insert(index, (priority, element))

    def remove(self, element):
        index = -1
        for i in xrange(len(self.queue)):
            if self.queue[i][1] is element:
                index = i
                break
        if index is not -1:
            del self.queue[index]

    def contains(self, element):
        for qe in self.queue:
            if qe[1] is element:
                return True
        return False

    def pop(self):
        return self.queue.pop()[1]

    def count(self):
        return len(self.queue)


class AssociativeList(object):
    """
    If a lightweight dictionary is needed, well here's one. Conserves memory and with low element counts
    conserves CPU as well.

    WHAT THE FUCK??? Python dictionaries would work just fine...
    """
    __slots__ = ["l"]

    def __init__(self):
        self.l = []

    def set(self, key, value):
        k = intern(key)
        for i in xrange(len(self.l)):
            if self.l[i][0] == k:
                self.l[i] = [k, value]
                return value
        self.l.append([k, value])
        return value

    def get(self, key):
        for i in xrange(len(self.l)):
            if self.l[i][0] == key:
                return self.l[i][1]
        return None

    def has(self, key):
        for i in xrange(len(self.l)):
            if self.l[i][0] == key:
                return True
        return False

    def inc(self, key, value):
        for i in xrange(len(self.l)):
            if self.l[i][0] == key:
                self.l[i][1] += value
                return self.l[i][1]
        return None

    def mul(self, key, value):
        for i in xrange(len(self.l)):
            if self.l[i][0] == key:
                self.l[i][1] *= value
                return self.l[i][1]
        return None

    def toggle(self, key):
        for i in xrange(len(self.l)):
            if self.l[i][0] == key:
                self.l[i][1] = not self.l[i][1]
                return self.l[i][1]
        return None

    def remove(self, key):
        index = -1
        value = None
        for i in xrange(len(self.l)):
            if self.e[i][0] == key:
                index = i
                break
        if index >= 0:
            value = self.l[index]
            del self.l[index]
        return value

    def clear(self):
        self.l = []

    def count(self):
        return len(self.l)

    def getDictionary(self):
        return {e[0]: e[1] for e in self.l}

    def __iter__(self):
        """
        Makes this object iterable. If you want to use indices, use assocList.l, which gives you the underlying list.
        """
        for e in self.l:
            yield e