from Search import *
import Enums
from euclid import Vector3


class Map(object):
    def __init__(self, nodes, search):
        self.nodes = [(id, nodes[id]) for id in range(len(nodes))]
        self.search = search

    def getNodeByID(self, id):
        return self.nodes[id]

    def findPath(self, startNode, endNode, data=None):
        return self.search.search(startNode, endNode, data)


class GridMap(Map):
    def __init__(self, width, height, grid, heightMap=None, search=None):
        d = lambda point, repelPoints: min(reduce(lambda s, p: s + (75/(point - p).magnitude_squared()), repelPoints, 0), 20) if repelPoints is not None else 0
        super(GridMap, self).__init__(
            [((grid[i], heightMap[i] if (heightMap is not None and len(heightMap) > 0) else 0.0), i%width, i/width) for i in xrange(len(grid))],
            AStar2(
                self.getNeighborsForNode,  # neighbor -function (fetches a list of neighbor nodes for a given node)
                lambda c, n, data: d(Vector3(n[Enums.NODE_DATA][Enums.GRIDNODE_X], n[Enums.NODE_DATA][Enums.GRIDNODE_Y]), data) +
                                   (50 if n[Enums.NODE_DATA][Enums.GRIDNODE_DATA][Enums.GRIDNODE_DATA_NODETYPE] is 1 else 1 if n[Enums.NODE_DATA][Enums.GRIDNODE_DATA][Enums.GRIDNODE_DATA_NODETYPE] is 2 else 1000),  # g -function (cost)
                lambda n, e, data: d(Vector3(e[Enums.NODE_DATA][Enums.GRIDNODE_X], e[Enums.NODE_DATA][Enums.GRIDNODE_Y]), data) +
                                   abs(e[Enums.NODE_DATA][Enums.GRIDNODE_X] - n[Enums.NODE_DATA][Enums.GRIDNODE_X]) +
                                   abs(e[Enums.NODE_DATA][Enums.GRIDNODE_Y] - n[Enums.NODE_DATA][Enums.GRIDNODE_Y])  # h -function (heuristic)
            ) if search is None else search)
        self.width = width
        self.height = height

    def getHeightMap(self):
        heightMap = []
        for y in xrange(self.height):
            for x in xrange(self.width):
                heightMap.append(float(self.nodes[x + y*self.width][Enums.NODE_DATA][Enums.GRIDNODE_DATA][Enums.GRIDNODE_DATA_HEIGHT]))
        return heightMap

    def getGridNode(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.nodes[x + y*self.width]
        return None

    def getGridNodeByWorldPos(self, worldPos):
        return self.getGridNode(int(worldPos.x), int(worldPos.y))

    def worldPosIsInside(self, worldPos):
        return (0 < worldPos.x < self.width) and (0 < worldPos.y < self.height)

    def worldPosIsOutside(self, worldPos):
        return not self.worldPosIsInside(worldPos)

    def getNeighborsForNode(self, node):
        if node is None:
            return []
        return filter(lambda n: n is not None, [
            self.getGridNode(node[Enums.NODE_DATA][Enums.GRIDNODE_X] - 1, node[Enums.NODE_DATA][Enums.GRIDNODE_Y] - 1),
            self.getGridNode(node[Enums.NODE_DATA][Enums.GRIDNODE_X]    , node[Enums.NODE_DATA][Enums.GRIDNODE_Y] - 1),
            self.getGridNode(node[Enums.NODE_DATA][Enums.GRIDNODE_X] + 1, node[Enums.NODE_DATA][Enums.GRIDNODE_Y] - 1),
            self.getGridNode(node[Enums.NODE_DATA][Enums.GRIDNODE_X] - 1, node[Enums.NODE_DATA][Enums.GRIDNODE_Y]    ),
            self.getGridNode(node[Enums.NODE_DATA][Enums.GRIDNODE_X] + 1, node[Enums.NODE_DATA][Enums.GRIDNODE_Y]    ),
            self.getGridNode(node[Enums.NODE_DATA][Enums.GRIDNODE_X] - 1, node[Enums.NODE_DATA][Enums.GRIDNODE_Y] + 1),
            self.getGridNode(node[Enums.NODE_DATA][Enums.GRIDNODE_X]    , node[Enums.NODE_DATA][Enums.GRIDNODE_Y] + 1),
            self.getGridNode(node[Enums.NODE_DATA][Enums.GRIDNODE_X] + 1, node[Enums.NODE_DATA][Enums.GRIDNODE_Y] + 1)
        ])

    def rayCast(self, start, end):
        results = []
        if start.x < 0:
            start.x = 0
        if start.x > self.width - 1:
            start.x = self.width - 1
        if start.y < 0:
            start.y = 0
        if start.y > self.height - 1:
            start.y = self.height - 1
        if end.x < 0:
            end.x = 0
        if end.x > self.width - 1:
            end.x = self.width - 1
        if end.y < 0:
            end.y = 0
        if end.y > self.height - 1:
            end.y = self.height - 1
        startNode = self.getGridNodeByWorldPos(start)
        endNode = self.getGridNodeByWorldPos(end)
        xStart = float(startNode[Enums.NODE_DATA][Enums.GRIDNODE_X])
        xEnd = float(endNode[Enums.NODE_DATA][Enums.GRIDNODE_X])
        yStart = float(startNode[Enums.NODE_DATA][Enums.GRIDNODE_Y])
        yEnd = float(endNode[Enums.NODE_DATA][Enums.GRIDNODE_Y])
        dx = xEnd - xStart
        dy = yEnd - yStart
        dxAbs = abs(dx)
        dyAbs = abs(dy)
        if dxAbs > dyAbs:
            steps = dxAbs
            if steps == 0.0:
                return [startNode]
            xInc = dx/steps
            yInc = dy/steps
            for i in range(int(steps)):
                x = int(xStart + i*xInc)
                y = int(yStart + i*yInc)
                results.append(self.nodes[x + y*self.width])
        else:
            steps = dyAbs
            if steps == 0.0:
                return [startNode]
            xInc = dx/steps
            yInc = dy/steps
            for i in range(int(steps)):
                x = int(xStart + i*xInc)
                y = int(yStart + i*yInc)
                results.append(self.nodes[x + y*self.width])
        results.append(endNode)
        return results
