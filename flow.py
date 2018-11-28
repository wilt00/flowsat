import itertools
import sys
import getopt
import fileinput
from z3 import *

EMPTY_CELL = "0"

def get_colors(grid):
    """
    Extract a list of colors from the grid
    """
    colors = []
    for row in grid:
        for cell in row:
            if cell != EMPTY_CELL and cell not in colors:
                colors.append(cell)
    return colors


def right_color_edge(color, edge_bool):
    """
    Test if a given edge variable is of the given color
    """
    return edge_bool.__str__().split("_")[-1] == color


def build_solver(grid):

    colors = get_colors(grid)
    edges = {}
    height = len(grid)
    width = len(grid[0])
    # Assume square grid
    #    j =  0   1
    # i = 0 | . | . |
    #           ^
    #         v0_0-1
    vert_edges = [f"v{i}_{j}-{j+1}"
                  for (i, j)
                  in itertools.product(range(height), range(width - 1))]
    #  .
    #  - < v 0-1_0
    #  .
    horiz_edges = [f"h{i}-{i+1}_{j}"
                   for (i, j)
                   in itertools.product(range(height - 1), range(width))]

    assert len(vert_edges) == len(horiz_edges)
    assert len(vert_edges) == (len(grid) - 1) * len(grid)

    edges = vert_edges + horiz_edges
    edge_vars = {}
    for edge in edges:
        edge_vars[edge] = []
        for color in colors:
            edge_vars[edge].append(Bool(f"{edge}_{color}"))

    def get_edge_vars(i, j):
        out = []
        if i > 0:
            out += edge_vars[f"h{i-1}-{i}_{j}"]
        if i < width - 1:
            out += edge_vars[f"h{i}-{i+1}_{j}"]
        if j > 0:
            out += edge_vars[f"v{i}_{j-1}-{j}"]
        if j < height - 1:
            out += edge_vars[f"v{i}_{j}-{j+1}"]
        return out

    solver = Solver()

    for (i, row) in enumerate(grid):
        for (j, cell) in enumerate(row):

            cell_edges = get_edge_vars(i, j)
            assert len(cell_edges) <= 4 * len(colors)

            if cell in colors:
                # Terminus

                # Let color = C, other colors = A,B
                #
                # For the wrong colored edges - one NOT term per edge:
                # ... AND NOT(e1_A) AND NOT(e1_B) AND ...
                #
                # For right colored edges - one OR term as follows:
                # ... AND ( (e1_C AND NOT e2_C AND NOT e3_C AND NOT e4_C)
                #           (NOT e1_c AND e2_C AND NOT e3_C ...

                t_edges_right = [e for e in cell_edges
                                 if right_color_edge(cell, e)]
                t_edges_wrong = [e for e in cell_edges
                                 if not right_color_edge(cell, e)]

                # Obviously can't have other colors cutting a terminus edge
                solver.add(*map(Not, t_edges_wrong))

                orterms = []
                for edge in t_edges_right:
                    otheredges = [Not(x) for x in t_edges_right
                                  if not x.__eq__(edge)]
                    orterms.append(And(edge, *otheredges))
                solver.add(Or(*orterms))

            else:
                # Cell

                # First Or term:
                # No lines enter this cell - single And term, Not all edges
                orterms = [(And(*map(Not, cell_edges)))]

                for color in colors:
                    # Each loop will generate at most 4C2 terms
                    cell_edges_c = [e for e in cell_edges
                                    if right_color_edge(color, e)]
                    # All of this Or section's terms for this color have this
                    # base: Not any of the other colors' edges
                    orterm_base = And(
                        *map(Not, [e for e in cell_edges
                                   if not right_color_edge(color, e)]))
                    for (e1, e2) in itertools.combinations(cell_edges_c, 2):
                        orterms.append(
                            And(e1, e2, orterm_base,
                                *map(Not, [e for e in cell_edges_c
                                           if e not in (e1, e2)])))
                solver.add(Or(*orterms))
    return solver


# def print_model(grid, model):


def main():
    """
    Main
    """
    # opts, _ = getopt.getopt(sys.argv[1:], "s", ["nospace"])
    splitchar = " "
    # for opt, _ in opts:
    #     if opt in ("-s", "--nospace"):
    #         splitchar = ""

    input_grid = []
    for line in fileinput.input():
        if fileinput.isfirstline():
            size = int(line)
        else:
            input_grid.append(line.strip().split(splitchar))

    print(input_grid)
    assert len(input_grid) == size
    assert len(input_grid[0]) == size

    solver = build_solver(input_grid)
    print(solver.check())
    # print(solver.model())

if __name__ == "__main__":
    main()
