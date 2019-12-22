from math import sqrt, cos, sin, pi
from shapely import geometry


class Hex:
    def __init__(self, pitch):
        self.pitch = pitch

    def __repr__(self):
        return f"{self.__class__.__name__}(pitch={self.pitch})"

    def polygon(self):
        nodes = [(self.pitch / sqrt(3.0) * cos((2.0 * i + 1.0) * pi / 6.0),
                  self.pitch / sqrt(3.0) * sin((2.0 * i + 1.0) * pi / 6.0)) for i in range(6)]
        return geometry.Polygon(nodes)


class Circle:
    def __init__(self, d):
        self.d = d

    def __repr__(self):
        return f"{self.__class__.__name__}(d={self.d})"

    def polygon(self):
        return geometry.Point(0.0, 0.0).buffer(self.d / 2.0)


class Rectangle:
    def __init__(self, length, width):
        self.length = length
        self.width = width

    def __repr__(self):
        return f"{self.__class__.__name__}(length={self.length}, width={self.width})"

    def polygon(self):
        nodes = [(self.length * cos((2.0 * i + 1.0) * pi / 4.0) / sqrt(2.0),
                  self.width * sin((2.0 * i + 1.0) * pi / 4.0) / sqrt(2.0)) for i in range(4)]
        return geometry.Polygon(nodes)
