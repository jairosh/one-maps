#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: Jairo Sanchez
# @Date:   2017-03-10 21:59:49
# @Last Modified by:   Jairo Sanchez
# @Last Modified time: 2017-03-15 13:38:41
"""Cleans graphs generated by osm4routing, keeps the largest
   connected component of the graph and writes it down to a
   .wkt file
"""
import networkx as nx
import argparse
import csv


G = nx.Graph()


def main():
    parsr = argparse.ArgumentParser(description='Cleans graphs for use in ONE')
    parsr.add_argument('-e', '--edges',
                       help='Edges file in CSV format',
                       required=False,
                       type=file,
                       default='edges.csv')
    parsr.add_argument('-v', '--vertex',
                       help='Vertex file in CSV format',
                       required=False,
                       type=file,
                       default='vertex.csv')
    parsr.add_argument('-o', '--outdir',
                       help='Output directory',
                       type=str,
                       required=False,
                       default='./')

    args = parsr.parse_args()
    load_nodes(args.vertex)
    load_edges(args.edges)
    largest_component = clean_graph()
    wkt_largest_c = get_wkt_from_graph(largest_component)

    write_graph(wkt_largest_c, "main.wkt")

    print "Finished"


def load_edges(edgesfile):
    edges_reader = csv.reader(edgesfile)
    for row in edges_reader:
        if row[0] == 'id':
            continue
        G.add_edge(row[1], row[2],
                   attr_dict={'id': row[0],
                              'length': float(row[3]),
                              'foot': int(row[4]),
                              'car_forward': int(row[5]),
                              'car_backward': int(row[6]),
                              'bike_forward': int(row[7]),
                              'bike_backward': int(row[8]),
                              'wkt': row[9]
                              })

    print '{0} edges added'.format(G.number_of_edges())


def load_nodes(nodesfile):
    nodes_reader = csv.reader(nodesfile)
    for row in nodes_reader:
        if row[0] == 'id':
            continue
        G.add_node(row[0], attr_dict={'lon': float(row[1]),
                                      'lat': float(row[2])})
    print '{0} nodes added'.format(G.number_of_nodes())


def clean_graph():
    subgraphs = list(nx.connected_component_subgraphs(G, copy=True))
    comp = max(nx.connected_component_subgraphs(G), key=len)
    print 'There\'s {0} connected subgraphs'.format(len(subgraphs))
    print 'Largest component has {0} nodes'.format(comp.number_of_nodes())

    largest_component = nx.Graph()
    cardinality = 0
    index = 0
    for graph in subgraphs:
        if graph.number_of_nodes() >= cardinality:
            largest_component = graph
            cardinality = graph.number_of_nodes()
        # if graph.number_of_nodes() >= 10:
        #     write_graph(graph, 'subgraph_{0}.wkt'.format(index))
        index = index + 1

    subgraphs.remove(largest_component)
    return largest_component


def get_wkt_from_graph(aGraph):
    graph_wkt = ''
    for edge in aGraph.edges():
        data = aGraph[edge[0]][edge[1]]['wkt'].split('(')
        # ONE requieres an space between the geometry type and the coords
        line = '{0} ({1}\n'.format(data[0], data[1])
        graph_wkt = graph_wkt + line

    return graph_wkt


def write_graph(WKTText, filename):
    with open(filename, 'wb') as outputfile:
        outputfile.write(WKTText)


if __name__ == '__main__':
    main()
