#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Draws the graphs created by emscan.py."""

import argparse
import logging

from colour import Color
import networkx as nx


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Draws the graphs created by emscan.py. Nodes are colored '
                    'with a gradient, based on the iteration they were added.')
    parser.add_argument('graphml_file', help='the graph in GraphML format.')
    parser.add_argument('output_file', help='the output (image-like) file.')
    parser.add_argument('--layout', '-l', type=str, default='circo',
                        choices=['neato', 'dot', 'twopi', 'circo', 'fdp'],
                        help='the positioning algorithm to use [circo].')
    parser.add_argument('--from-color', '-f', type=str, default='red',
                        help='the node color for the original points; '
                             'one end of the gradient [red].')
    parser.add_argument('--to-color', '-t', type=str, default='yellow',
                        help='the node color for the points added in the last '
                             'iteration; the other end of the gradient [yellow].')
    parser.add_argument('--log-level', '-L', type=str, default='critical',
                        choices=['debug', 'info', 'warning', 'error', 'critical'],
                        help='the logging level [critical].')

    args = parser.parse_args()
    return args


def remove_impotent(G):
    """Removes all nodes from the initial iteration with no successors."""
    to_delete = [node for node, data in G.nodes(data=True)
                 if data['it'] == 0 and not list(nx.all_neighbors(G, node))]
    print(to_delete)
    G.remove_nodes_from(to_delete)


def main():
    args = parse_arguments()
    logging.basicConfig(level=getattr(logging, args.log_level.upper()),
                        format='%(asctime)s - %(levelname)s - %(message)s')

    G = nx.reverse(nx.read_graphml(args.graphml_file))
    num_colors = len(set(d['it'] for _, d in G.nodes(data=True)))
    colors = list(
        Color(args.from_color).range_to(Color(args.to_color), num_colors + 1))
    del colors[1]
    remove_impotent(G)
    for node, data in G.nodes(data=True):
        G.node[node]['color'] = colors[data['it']].get_hex_l()
    A = nx.nx_agraph.to_agraph(G)
    A.node_attr['style'] = 'filled'
    A.draw(args.output_file, prog=args.layout)


if __name__ == '__main__':
    main()
