from math import sqrt
from assembly_classes import Hex
from shapely import affinity, geometry
from lattice_classes import HexLattice


class PinMesh:
    def __init__(self, pins, pitch):
        self.pins = pins
        self.pitch = pitch

    def get_mesh(self):
        coord = HexLattice(pitch=self.pitch, pattern=[0] * self.pins).spiral_coord()
        pin_mesh = []
        poly = affinity.rotate(Hex(self.pitch + 1e-10).polygon(), angle=30, use_radians=False)
        for i in range(len(coord)):
            pin_mesh.append(affinity.translate(poly, xoff=coord[i][0], yoff=coord[i][1]))
        return pin_mesh


class RhombMesh:
    def __init__(self, submesh):
        self.submesh = submesh

    def get_mesh(self):
        # get number of cells
        num_rows = len(self.submesh) - 1
        # (u, v)
        pin_mesh = []
        for j in range(num_rows - 1, -1, -1):
            for i in range(num_rows - 1, -1, -1):
                poly = geometry.Polygon([(self.submesh[i + 1], self.submesh[j + 1] * sqrt(3) / 2),
                                         (self.submesh[i], self.submesh[j + 1] * sqrt(3) / 2),
                                         (self.submesh[i], self.submesh[j] * sqrt(3) / 2),
                                         (self.submesh[i + 1], self.submesh[j] * sqrt(3) / 2)])
                poly = affinity.skew(poly, xs=-30, origin=(0, 0))
                poly = affinity.rotate(poly, angle=-150, origin=(0, 0), use_radians=False)
                pin_mesh.append(poly)
        # (w, u)
        for j in range(num_rows):
            for i in range(num_rows - 1, -1, -1):
                poly = geometry.Polygon([(self.submesh[i + 1] * sqrt(3) / 2, self.submesh[j + 1]),
                                         (self.submesh[i] * sqrt(3) / 2, self.submesh[j + 1]),
                                         (self.submesh[i] * sqrt(3) / 2, self.submesh[j]),
                                         (self.submesh[i + 1] * sqrt(3) / 2, self.submesh[j])])
                poly = affinity.scale(poly, xfact=-1, origin=(0, 0))
                poly = affinity.skew(poly, ys=30, origin=(0, 0))
                pin_mesh.append(poly)
        # (v, w)
        for j in range(num_rows):
            for i in range(num_rows):
                poly = geometry.Polygon([(self.submesh[i + 1] * sqrt(3) / 2, self.submesh[j + 1]),
                                         (self.submesh[i] * sqrt(3) / 2, self.submesh[j + 1]),
                                         (self.submesh[i] * sqrt(3) / 2, self.submesh[j]),
                                         (self.submesh[i + 1] * sqrt(3) / 2, self.submesh[j])])
                poly = affinity.skew(poly, ys=-30, origin=(0, 0), use_radians=False)
                pin_mesh.append(poly)
        return pin_mesh
