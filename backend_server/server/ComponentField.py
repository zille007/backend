import sys

class ComponentField(object):
    def fromString(self, value):
        return value

    def toRange(self, value):
        return value

    def isInRange(self, value):
        return True

    def __init__(self, default = None):
        self.default = default


class FloatValue( ComponentField ):
    def fromString(self, value):
        return float(value)

    def toRange(self, value):
        v = min( self.maxValue, value )
        v = max( self.minValue, v )
        return v

    def isInRange(self, value):
        if value >= self.minValue and value <= self.maxValue:
            return True
        return False

    def __init__(self, default = 0.0, minValue = float("-inf"), maxValue = float("inf") ):
        super(FloatValue, self).__init__(default)
        self.minValue = minValue
        self.maxValue = maxValue


class IntegerValue( ComponentField ):
    def fromString(self, value):
        return int(value)

    def toRange(self, value):
        v = min( self.maxValue, value )
        v = max( self.minValue, v )
        return v

    def isInRange(self, value):
        if value >= self.minValue and value <= self.maxValue:
            return True
        return False

    def __init__(self, default = 0, minValue = -sys.maxint - 1, maxValue = sys.maxint ):
        super(IntegerValue, self).__init__(default)
        self.minValue = minValue
        self.maxValue = maxValue


class StringValue( ComponentField ):
    def fromString(self, value):
        return value

    def toRange( self, value ):
        return value[0:self.maxLength]

    def isInRange( self, value ):
        if len(value) > self.maxLength:
            return False

        return True

    def __init__(self, default = "", maxLength = -1 ):
        super(StringValue, self).__init__(default)
        self.maxLength = maxLength


class BooleanValue( ComponentField ):
    def fromString(self, value):
        return bool(value)

    def toRange( self, value ):
        return value

    def isInRange( self, value ):
        return True

    def __init__(self, default = True ):
        super(BooleanValue, self).__init__(default)

