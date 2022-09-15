from Intersection import circleToSquare
from euclid import Vector3
import Enums


class SpatialHash(object):
    def __init__(self, width, height, bucketSize):
        self.width = width
        self.height = height
        self.bucketSize = bucketSize
        self.bucketsX = self.width/self.bucketSize + (1 if self.width%self.bucketSize > 0 else 0)
        self.bucketsY = self.height/self.bucketSize + (1 if self.height%self.bucketSize > 0 else 0)
        self.bucketGrid = [[] for y in xrange(self.bucketsY) for x in xrange(self.bucketsX)]
        self.count = 0

    def getBucketsByAABB(self, lowerLeft, width, height):
        ## TODO
        return []

    def getBucketsByCircle(self, circleWorldPos, circleRadius):
        bucketSizedWorldPos = circleWorldPos/self.bucketSize
        bucketSizedRadius = circleRadius/self.bucketSize

        x_lower = int(bucketSizedWorldPos.x - bucketSizedRadius)
        x_upper = int(bucketSizedWorldPos.x + bucketSizedRadius) + 1
        y_lower = int(bucketSizedWorldPos.y - bucketSizedRadius)
        y_upper = int(bucketSizedWorldPos.y + bucketSizedRadius) + 1

        if x_lower < 0: x_lower = 0
        if x_upper >= self.bucketsX: x_upper = self.bucketsX
        if y_lower < 0: y_lower = 0
        if y_upper >= self.bucketsY: y_upper = self.bucketsY

        return [self.getBucket(x, y)
                for y in xrange(y_lower, y_upper)
                for x in xrange(x_lower, x_upper)
                if circleToSquare(circleWorldPos, circleRadius, Vector3(x*self.bucketSize, y*self.bucketSize, 0), self.bucketSize)]

    def getBucketByPoint(self, worldPos):
        if 0 <= worldPos.x < self.width and 0 <= worldPos.y < self.height:
            bucketPos = (worldPos/self.bucketSize)
            bucket_x = int(bucketPos.x)
            bucket_y = int(bucketPos.y)
            return self.bucketGrid[bucket_x + bucket_y*self.bucketsX]
        return None

    def getBucket(self, bucket_x, bucket_y):
        if 0 <= bucket_x < self.bucketsX and 0 <= bucket_y < self.bucketsY:
            return self.bucketGrid[bucket_x + bucket_y*self.bucketsX]
        return None

    def compareBuckets(self, bucketsA, bucketsB):
        if len(bucketsA) is not len(bucketsB):
            return False

        for i in xrange(len(bucketsA)):
            if bucketsA[i] is not bucketsB[i]:
                return False

        return True

    def removeFromBuckets(self, buckets, phys):
        for bucket in buckets:
            try:
                bucket.remove(phys)
            except ValueError:
                continue

    def addToBuckets(self, buckets, phys):
        for bucket in buckets:
            bucket.append(phys)

    def addPhysical(self, phys):
        self.count += 1
        pos = phys.entity.getComponent(Enums.COMP_TYPE_TRANSFORM).getWorldPosition()
        for s in phys.shapes:
            if s[Enums.PHYS_SHAPE] is Enums.SHAPE_TYPE_POINT:
                bucket = self.getBucketByPoint(pos + s[Enums.PHYS_CENTER])
                if bucket is None:
                    continue
                if phys not in bucket:
                    bucket.append(phys)
                    continue
            elif s[Enums.PHYS_SHAPE] is Enums.SHAPE_TYPE_CIRCLE:
                buckets = self.getBucketsByCircle(pos + s[Enums.PHYS_CENTER], s[Enums.PHYS_CIRCLE_RADIUS])
                for bucket in buckets:
                    if phys not in bucket:
                        bucket.append(phys)
            elif s[Enums.PHYS_SHAPE] is Enums.SHAPE_TYPE_AABB:
                pass

    def removePhysical(self, phys):
        found = False
        pos = phys.entity.getComponent(Enums.COMP_TYPE_TRANSFORM).getWorldPosition()
        for s in phys.shapes:
            if s[0] is Enums.SHAPE_TYPE_POINT:
                bucket = self.getBucketByPoint(pos + s[1])
                if bucket is None:
                    continue
                try:
                    bucket.remove(phys)
                    found = True
                except ValueError:
                    continue
            elif s[0] is Enums.SHAPE_TYPE_CIRCLE:
                for bucket in self.getBucketsByCircle(pos + s[1], s[2]):
                    try:
                        bucket.remove(phys)
                        found = True
                    except ValueError:
                        continue
            elif s[0] is Enums.SHAPE_TYPE_AABB:
                pass
        if found:
            self.count -= 1

    def clear(self):
        for l in self.bucketGrid:
            del l[:]
        self.count = 0

    def intersectPoint(self, worldPos):
        bucket = self.getBucketByPoint(worldPos)
        if bucket is not None:
            for phys in bucket:
                if phys.intersectsPoint(worldPos):
                    return True
        return False

    def intersectCircle(self, worldPos, radius):
        for bucket in self.getBucketsByCircle(worldPos, radius):
            for phys in bucket:
                if phys.intersectsCircle(worldPos, radius):
                    return True
        return False

    def intersectAABB(self, lowerLeft, width, height):
        for bucket in self.getBucketsByAABB(lowerLeft, width, height):
            for phys in bucket:
                if phys.intersectsAABB(lowerLeft, width, height):
                    return True
        return False

    def queryPoint(self, worldPos):
        bucket = self.getBucketByPoint(worldPos)
        result = []
        if bucket is not None:
            for phys in bucket:
                if phys not in result:
                    if phys.intersectsPoint(worldPos):
                        result.append(phys)
        return result

    def queryCircle(self, worldPos, radius):
        buckets = self.getBucketsByCircle(worldPos, radius)
        result = []
        for bucket in buckets:
            for phys in bucket:
                if phys not in result:
                    if phys.intersectsCircle(worldPos, radius):
                        result.append(phys)
        return result

    def queryAABB(self, lowerLeft, width, height):
        buckets = self.getBucketsByAABB(lowerLeft, width, height)
        result = []
        for bucket in buckets:
            for phys in bucket:
                if phys not in result:
                    if phys.intersectsAABB(lowerLeft, width, height):
                        result.append(phys)
        return result

    def updatePhysical(self, phys):
        newPos = phys.entity.getComponent(Enums.COMP_TYPE_TRANSFORM).getWorldPosition()
        oldPos = phys.entity.getComponent(Enums.COMP_TYPE_TRANSFORM).oldPosition

        if oldPos == newPos:
            return

        oldBuckets = []
        for s in phys.shapes:
            if s[0] is Enums.SHAPE_TYPE_POINT:
                bucket = self.getBucketByPoint(oldPos + s[1])
                if bucket is not None:
                    oldBuckets.append(bucket)
            elif s[0] is Enums.SHAPE_TYPE_CIRCLE:
                oldBuckets += self.getBucketsByCircle(oldPos + s[1], s[2])
            elif s[0] is Enums.SHAPE_TYPE_AABB:
                oldBuckets += self.getBucketsByAABB(oldPos + s[1], s[2], s[3])
        newBuckets = []
        for s in phys.shapes:
            if s[0] is Enums.SHAPE_TYPE_POINT:
                bucket = self.getBucketByPoint(newPos + s[1])
                if bucket is not None:
                    newBuckets.append(bucket)
            elif s[0] is Enums.SHAPE_TYPE_CIRCLE:
                newBuckets += self.getBucketsByCircle(newPos + s[1], s[2])
            elif s[0] is Enums.SHAPE_TYPE_AABB:
                newBuckets += self.getBucketsByAABB(newPos + s[1], s[2], s[3])
        if self.compareBuckets(oldBuckets, newBuckets):
            return

        self.removeFromBuckets(oldBuckets, phys)
        self.addToBuckets(newBuckets, phys)