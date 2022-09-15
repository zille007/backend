import txmongo
from twisted.internet import defer, reactor
from utils import dict_miss, print_dict


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
    print "MongoMiss script v0.3"
    print ""
    print "###########################"
    print "### Missing in 10.0.0.1 ###"
    print "###########################"
    print ""
    for a in a_list:
        name = a["name"]
        a = a["components"]
        p = findPrefab(name, b_list)
        if p is None:
            print name + " -prefab missing"
            continue
        b = p["components"]
        if b is not None:
            d = dict_miss(a, b)
            if d is not None:
                print name + ":"
                print_dict(d)
                print ""
    print ""
    print "############################"
    print "### Missing in 127.0.0.1 ###"
    print "############################"
    print ""
    for b in b_list:
        name = b["name"]
        b = b["components"]
        p = findPrefab(name, a_list)
        if p is None:
            print name + " -prefab missing"
            continue
        a = p["components"]
        if a is not None:
            d = dict_miss(b, a)
            if d is not None:
                print name + ":"
                print_dict(d)
                print ""