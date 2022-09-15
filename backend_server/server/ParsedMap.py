from euclid import *
from utils import listToVector
import string


class ParsedMap(object):
    def isLegalMap(self):
        if self.name == "__undefined":
            return False

        return True

    def getMapDictionary(self):
        return {
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "tilesize": self.tilesize,
            "origin": tuple(self.origin),
            "map": string.join(self.tiles, "\n"),
            "heightMap": self.heightMap,
            "structures": self.structures,
            "props": self.props
        }

    def parseMapDictionary(self, mapdef):
        baseattribs = [ "name", "width", "height", "tilesize" ]
        for attrib in baseattribs:
            if mapdef.has_key(attrib):
                self.__dict__[attrib] = mapdef[attrib]

        origin_vec = None
        if mapdef.has_key( "origin" ):
            origin_vec = listToVector( mapdef["origin"] )
            self.origin = origin_vec

        if mapdef.has_key( "map" ):
            mapstr = mapdef["map"]
            self.tiles = mapstr.split("\n")

        if mapdef.has_key("heightMap"):
            self.heightMap = mapdef["heightMap"]

        if mapdef.has_key( "structures" ):
            self.structures = mapdef["structures"]

        if mapdef.has_key( "props" ):
            self.props = mapdef["props"]

    def __init__(self, mapdef = None):
        self.name = "__undefined"
        self.width = 0
        self.height = 0
        self.tilesize = 1.0
        self.origin = Vector3(0.0, 0.0, 0.0)
        self.tiles = []
        self.heightMap = []
        self.structures = []
        self.props = []

        if mapdef is not None:
            self.parseMapDictionary( mapdef )