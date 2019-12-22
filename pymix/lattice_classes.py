from math import sqrt, sin, cos, pi, ceil


class HexLattice:
    def __init__(self, pitch, pattern):
        self.pitch = pitch
        self.pattern = pattern

    def num_nodes(self):
        return len(self.pattern)

    def num_rings(self):
        return ceil((1 + sqrt(1 + 4 / 3 * (self.num_nodes() - 1))) / 2)

    def spiral_coord(self):
        coord = [(0.0, 0.0)] * self.num_nodes()

        for i in range(1, self.num_rings()):
            for j in range(6):
                coord[3 * i * (i - 1) + 2 + j * i - 1] = (self.pitch * i * cos(j / 3.0 * pi + pi / 6.0),
                                                          self.pitch * i * sin(j / 3.0 * pi + pi / 6.0))
            if i > 1:
                for j in range(5):
                    a = 3 * i * (i - 1) + 2 + i * j - 1
                    b = a + i
                    for k in range(1, i):
                        coord[a + k] = (coord[a][0] + (coord[b][0] - coord[a][0]) / i * k,
                                        coord[a][1] + (coord[b][1] - coord[a][1]) / i * k)
                a = 3 * i * (i - 1) + 2 + i * 5 - 1
                b = 3 * i * (i - 1) + 2 + i * 0 - 1
                for k in range(1, i):
                    coord[a + k] = (coord[a][0] + (coord[b][0] - coord[a][0]) / i * k,
                                    coord[a][1] + (coord[b][1] - coord[a][1]) / i * k)
        return coord


class RectangularLattice:
    def __init__(self, nx, ny, dx, dy, pattern):
        self.nx = nx
        self.ny = ny
        self.dx = dx
        self.dy = dy
        self.pattern = pattern

    def get_coord(self):
        coord = []
        for i in range(self.nx):
            for j in range(self.ny):
                coord.append(((i + 1) * self.dx, (j + 1) * self.dy))
        return coord


class CircleLattice:
    def __init__(self, nodes, pitch, pattern):
        self.nodes = nodes
        self.pitch = pitch
        self.pattern = pattern

    def get_coord(self):
        coord = []
        angle = 360.0 / self.nodes / 180.0 * pi
        for i in range(self.nodes):
            coord.append((0.5 * self.pitch * cos(i * angle), 0.5 * self.pitch * sin(i * angle)))
        return coord
