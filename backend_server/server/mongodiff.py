import txmongo
from twisted.internet import defer, reactor
from utils import dict_diff, print_dict


@defer.inlineCallbacks
def queryCollection(database, collection, ip, results):
    mongo = yield txmongo.MongoConnection(ip, 27017)
    queryResult = yield mongo.tatd.prefabs.find()
    results += queryResult


def findPrefab(prefabName, prefabs):
    for p in prefabs:
        if p["name"] == prefabName:
            return {"name": p["name"], "components": p["components"]}
    return None


if __name__ == '__main__':
    a_list = []
    b_list = []
    queryCollection("tatd", "prefabs", "127.0.0.1", a_list)
    queryCollection("tatd", "prefabs", "10.0.0.1", b_list).addCallback(lambda ign: reactor.stop())
    reactor.run()
    print "MongoDiff script v0.3"
    print ""
    print "#############################"
    print "### 127.0.0.1 -> 10.0.0.1 ###"
    print "#############################"
    print ""
    for a in a_list:
        name = a["name"]
        a = a["components"]
        try:
            b = findPrefab(name, b_list)["components"]
        except TypeError:
            print name + " -prefab missing on 10.0.0.1"
            continue
        if b is not None:
            d = dict_diff(a, b)
            if d is not None:
                print name + ":"
                print_dict(d)
                print ""