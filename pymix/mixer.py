import sys
import csv
import yaml
import assembly_classes as asm
import matplotlib.pyplot as plt
from shapely import affinity, geometry
from shapely.ops import cascaded_union
from descartes import PolygonPatch
import lattice_classes
import mesh_classes
from math import sqrt
from collections import OrderedDict as od
import time


def main():
    filename = sys.argv[-1] if len(sys.argv) > 1 else sys.stdin.readline().strip()

    start = time.time()
    with open(filename, 'r', encoding='utf-8') as input_file:
        content = yaml.load(input_file, Loader=yaml.FullLoader)

    # geometry elements
    geom_elements = {}
    for elem in content['Geom_elements']:
        # basis elements
        if 'shape' in elem.keys():
            if elem['shape'] == 'hex':
                poly = asm.Hex(pitch=elem['size']).polygon()
            elif elem['shape'] == 'circle':
                poly = asm.Circle(d=elem['size']).polygon()
            elif elem['shape'] == 'rectangle':
                poly = asm.Rectangle(length=elem['size'][0], width=elem['size'][1]).polygon()
            elif elem['shape'] == 'square':
                poly = asm.Rectangle(length=elem['size'], width=elem['size']).polygon()
        # combined elements
        if 'intersection' in elem.keys():
            poly = geom_elements[elem['intersection'][0]]
            for id in elem['intersection']:
                poly = geometry.Polygon.intersection(poly, geom_elements[id])
        if 'union' in elem.keys():
            poly = geometry.Polygon()
            for id in elem['union']:
                poly = geometry.Polygon.union(poly, geom_elements[id])
        if 'difference' in elem.keys():
            poly = geom_elements[elem['difference'][0]]
            if len(elem['difference']) > 1:
                for item in elem['difference'][1:]:
                    poly = geometry.Polygon.difference(poly, geom_elements[item])
        # lattices
        if 'lattice' in elem.keys():
            if elem['lattice'] == 'hex':
                coord = lattice_classes.HexLattice(elem['pitch'], elem['pattern']).spiral_coord()
            if elem['lattice'] == 'box':
                coord = lattice_classes.RectangularLattice(nx=elem['nodes'][0], ny=elem['nodes'][1],
                                                           dx=elem['pitch'][0], dy=elem['pitch'][1],
                                                           pattern=elem['pattern']).get_coord()
            if elem['lattice'] == 'circle':
                coord = lattice_classes.CircleLattice(nodes=elem['nodes'], pitch=elem['pitch'],
                                                      pattern=elem['pattern']).get_coord()
            poly = geometry.MultiPolygon([affinity.translate(geom_elements[id], xoff=coord[i][0], yoff=coord[i][1])
                                          for i, id in enumerate(elem['pattern']) if id in geom_elements.keys()])
        # rotation & translation
        if 'rotation' not in elem.keys():
            elem.update({'rotation': 0})
        if 'translation' not in elem.keys():
            elem.update({'translation': [0, 0]})
        poly = affinity.rotate(poly, angle=elem['rotation'], origin='centroid', use_radians=False)
        poly = affinity.translate(poly, xoff=elem['translation'][0], yoff=elem['translation'][1])
        if elem['id'] in geom_elements.keys():
            elem['id'] = f"{elem['id']}_"
        else:
            geom_elements[elem['id']] = poly

    # physical elements
    phys_elements = [(elem['mat'], geom_elements[elem['id']]) for elem in content['Physical_elements']]

    # assembly cell
    if content['Assembly_cell']['shape'] == 'hex':
        asm_cell = asm.Hex(pitch=content['Assembly_cell']['pitch']).polygon()
    elif content['Assembly_cell']['shape'] == 'square':
        asm_cell = asm.Rectangle(length=content['Assembly_cell']['pitch'], width=content['Assembly_cell']['pitch']).polygon()
    # coolant
    coolant = [content['Assembly_cell']['mat'], asm_cell]
    for _mat, poly in phys_elements:
        coolant[1] = coolant[1].difference(poly)

    # hex_mesh
    pin_mesh = mesh_classes.PinMesh(content['Pin_mesh']['pins'], content['Pin_mesh']['pitch']).get_mesh()
    pin_area = sqrt(3) / 2 * content['Pin_mesh']['pitch'] ** 2
    num_pins = len(pin_mesh)

    print(f"read *.yml: {time.time() - start:.4f} seconds")

    # boundary layer
    bound_layer = asm_cell.difference(cascaded_union(pin_mesh))
    bound_area = bound_layer.area

    # all physical elements including coolant
    phys_elements += [(coolant[0], coolant[1])]

    start = time.time()

    # boundary fraction
    bound_fraction = {mat: 0 for mat, poly in phys_elements}
    for mat, poly in phys_elements:
        bound_fraction[mat] += bound_layer.intersection(poly).area / bound_area

    # fractions
    fractions = [{mat: 0 for mat, _ in phys_elements} for _ in range(num_pins)]
    for i, fraction in enumerate(fractions):
        for mat, poly in phys_elements:
            if pin_mesh[i].intersects(poly):
                fraction[mat] += pin_mesh[i].intersection(poly).area / pin_area
    fractions.append(bound_fraction)

    print(f"calculate fractions: {time.time() - start:.4f} seconds")
    start = time.time()

    # rounding up to 5 significant digits
    for fraction in fractions:
        for key, value in fraction.items():
            fraction[key] = round(value, 5)

    # new materials id's
    unique_fractions = [dict(y) for y in set(tuple(x.items()) for x in fractions)]
    new_mat_num = [0] * len(fractions)
    for i, item in enumerate(fractions):
        for j, unique_item in enumerate(unique_fractions):
            if item == unique_item:
                new_mat_num[i] = j

    # csv output
    fields = ['spiral_number']
    for k in sorted(fractions[0].keys()):
        fields.append(k)
    fields.append('new_mat_id')
    try:
        with open(filename[0:filename.index('.')] + '_fractions.csv', 'w', newline='') as f:
            w = csv.DictWriter(f, fields, delimiter=';')
            w.writeheader()
            for i, fraction in enumerate(fractions):
                row = {'spiral_number': i + 1}
                row.update(fraction)
                row.update({'new_mat_id': new_mat_num[i]})
                w.writerow(row)
    except IOError:
        raise Warning("close .csv file before running Pymix")

    # colors
    norm = plt.Normalize()
    mat_list = list(od.fromkeys([mat for mat, _ in phys_elements]).keys())

    colors = plt.cm.rainbow(norm([mat_list.index(mat) for mat, _ in phys_elements]))
    # print(colors * 2)
    pin_color = [0] * num_pins
    for i in range(num_pins):
        for k, v in fractions[i].items():
           pin_color[i] += mat_list.index(k) * v

    # boundary cell color
    bound_color = 0
    for k, v in bound_fraction.items():
        bound_color += colors[mat_list.index(k)] * v

    # material area
    area = {mat: 0 for mat, poly in phys_elements}
    for mat, poly in phys_elements:
        area[mat] += poly.area

    # additional csv output
    try:
        with open(filename[0:filename.index('.')] + '_fractions_add.csv', 'w', newline='') as f:
            w = csv.DictWriter(f, fields, delimiter=';')
            w.writeheader()
            for i, fraction in enumerate(fractions):
                for k, v in fraction.items():
                    if i == num_pins:
                        fraction[k] = v * bound_layer.area / area[k]
                    else:
                        fraction[k] = v * pin_area / area[k]
                row = {'spiral_number': i + 1}
                row.update(fraction)
                row.update({'new_mat_id': new_mat_num[i]})
                w.writerow(row)
    except IOError:
        print("Warning: close .csv file before running Pymix")

    print(f"write *.csv: {time.time() - start:.4f} seconds")
    start = time.time()

    fig, ax = plt.subplots(1, 3, subplot_kw=dict(aspect='equal'))
    for i, (_, poly) in enumerate(phys_elements):
        ax[0].add_patch(PolygonPatch(polygon=poly, facecolor=colors[i], alpha=1.0, linewidth=0.0))
        ax[1].add_patch(PolygonPatch(polygon=poly, facecolor=colors[i], alpha=1.0, linewidth=0.0))
    colors = plt.cm.rainbow(norm(pin_color))
    for i, item in enumerate(pin_mesh):
        ax[2].add_patch(PolygonPatch(bound_layer, facecolor="springgreen", alpha=1.0, linewidth=0.5))
        ax[2].add_patch(PolygonPatch(item, facecolor=colors[i], alpha=1.0, linewidth=0.5))
        ax[1].add_patch(PolygonPatch(item, fill=False, linewidth=0.5))

    for item in ax:
        item.autoscale_view()
        item.set_yticklabels([])
        item.set_xticklabels([])
        item.tick_params(axis=u'both', which=u'both', length=0)

    plt.subplots_adjust(wspace=0.05, top=1.00, bottom=0.00, left=0.04, right=0.99)

    fig = plt.gcf()
    fig.set_size_inches((8.5, 11), forward=False)
    fig.savefig(filename[0:filename.index('.')] + '.png', dpi=500, bbox_inches='tight')
    # manager = plt.get_current_fig_manager()
    # manager.resize(*manager.window.maxsize())

    print(f"plot: {time.time() - start:.4f} seconds")

    plt.show()


if __name__ == '__main__':
    main()
