from euclid import Vector3
import math


def cross2D(v1, v2):
    return v1.x*v2.y - v1.y*v2.x


def pointToCircle(point, circleWorldPos, circleRadius):
    return (circleWorldPos - point).magnitude_squared() <= circleRadius**2


def circleToCircle(circleAWorldPos, circleARadius, circleBWorldPos, circleBRadius):
    return (circleBWorldPos - circleAWorldPos).magnitude_squared() <= (circleARadius + circleBRadius)**2


def lineSegmentToLineSegment(line1Start, line1End, line2Start, line2End):
    l1 = line1End - line1Start
    l2 = line2End - line2Start
    startDiff = line2Start - line1Start
    l1l2Cross = cross2D(l1, l2)
    if l1l2Cross == 0.0:
        if cross2D(startDiff, l1) != 0.0:
            return False
        else:
            ## TODO need to check if collinear line segments overlap
            return False
    s1 = cross2D(startDiff, l2)/l1l2Cross
    s2 = cross2D(startDiff, l1)/l1l2Cross
    return (0 <= s1 <= 1) and (0 <= s2 <= 1)


def lineInfToCircle(point1, point2, center, radius):
    p1 = point1 - center
    p2 = point2 - center
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    dr_sqr = dx**2 + dy**2
    D = p1.x*p2.y - p2.x*p1.y
    return ((radius**2) * dr_sqr) - (D**2) >= 0


def lineSegmentToCircle(start, end, center, radius):
    p1 = start - center
    p2 = end - center
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    dr_sqr = dx**2 + dy**2
    D = p1.x*p2.y - p2.x*p1.y
    if ((radius**2) * dr_sqr) - (D**2) >= 0:
        if p1.magnitude_squared() <= radius**2:
            return True
        if p2.magnitude_squared() <= radius**2:
            return True
        unit = (p2 - p1).normalized()
        if (unit.dot(p1) < 0.0 < unit.dot(p2)) or (unit.dot(p2) < 0.0 < unit.dot(p1)):
            return True
    return False


def lineInfToCircleIntersectionPoints(point1, point2, center, radius):
    p1 = point1 - center
    p2 = point2 - center
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    dr_sqr = dx**2 + dy**2
    D = p1.x*p2.y - p2.x*p1.y
    delta = ((radius**2) * dr_sqr) - (D**2)
    if delta > 0.0:
        return (
            Vector3((D*dy + (dy/abs(dy))*dx*math.sqrt(delta))/dr_sqr, (-D*dx + abs(dy)*math.sqrt(delta))/dr_sqr),
            Vector3((D*dy - (dy/abs(dy))*dx*math.sqrt(delta))/dr_sqr, (-D*dx - abs(dy)*math.sqrt(delta))/dr_sqr),
        )
    elif delta == 0.0:
        return Vector3(D*dy/dr_sqr, -D*dx/dr_sqr),
    return ()


def pointToSquare(point, squareLowerLeft, squareSide):
    return (squareLowerLeft.x <= point.x <= squareLowerLeft.x + squareSide and
            squareLowerLeft.y <= point.y <= squareLowerLeft.y + squareSide)


def circleToSquare(circleWorldPos, circleRadius, squareLowerLeft, squareSide):
    xSide = 1
    ySide = 1

    if circleWorldPos.x < squareLowerLeft.x:
        xSide = 0
    elif circleWorldPos.x > squareLowerLeft.x + squareSide:
        xSide = 2

    if circleWorldPos.y < squareLowerLeft.y:
        ySide = 0
    elif circleWorldPos.y > squareLowerLeft.y + squareSide:
        ySide = 2

    quadrant = xSide + ySide*3
    quadrantChecks = [# lower left
                      lambda: (squareLowerLeft - circleWorldPos).magnitude_squared() <= circleRadius**2,

                      # lower center
                      lambda: squareLowerLeft.y - circleWorldPos.y <= circleRadius,

                      # lower right
                      lambda: ((squareLowerLeft + Vector3(squareSide, 0, 0)) - circleWorldPos).magnitude_squared() <= circleRadius**2,

                      # middle left
                      lambda: squareLowerLeft.x - circleWorldPos.x <= circleRadius,

                      # center
                      lambda: True,

                      # middle right
                      lambda: circleWorldPos.x - (squareLowerLeft.x + squareSide) <= circleRadius,

                      # upper left
                      lambda: ((squareLowerLeft + Vector3(0, squareSide, 0)) - circleWorldPos).magnitude_squared() <= circleRadius**2,

                      # upper center
                      lambda: circleWorldPos.y - (squareLowerLeft.y + squareSide) <= circleRadius,

                      # upper right
                      lambda: ((squareLowerLeft + Vector3(squareSide, squareSide, 0)) - circleWorldPos).magnitude_squared() <= circleRadius**2]
    return quadrantChecks[quadrant]()


def lineSegmentToSquare(lineStart, lineEnd, squareLowerLeft, squareSide):
    if pointToSquare(lineStart, squareLowerLeft, squareSide) or pointToSquare(lineEnd, squareLowerLeft, squareSide):
        return True



def pointToAABB(worldPos, lowerLeft, width, height):
    return (lowerLeft.x <= worldPos.x <= lowerLeft.x + width) and (lowerLeft.y <= worldPos.y <= lowerLeft.y + height)


def circleToAABB(circleWorldPos, circleRadius, AABBlowerLeft, AABBwidth, AABBheight):
    # TODO
    return False


def AABBToAABB(AABBlowerLeftA, AABBwidthA, AABBheightA, AABBlowerLeftB, AABBwidthB, AABBheightB):
    # TODO
    return False