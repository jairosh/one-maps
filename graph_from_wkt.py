#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: Jairo Sanchez
# @Date:   2017-03-23 08:06:30
# @Last Modified by:   Jairo Sanchez
# @Last Modified time: 2017-03-23 18:52:10
import networkx as nx
import argparse
import re
from geomet import wkt
import os
import logging

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


all_geometries = []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input',
                        type=str,
                        help='Input WKT file',
                        required=True)
    parser.add_argument('-o', '--outputDir',
                        type=str,
                        help='Target directory to save all the graphs',
                        required=True)
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        logging.error('%s does not exist', args.input)        
        exit(1)

    if not os.path.isdir(args.outputDir):
        os.makedirs(args.outputDir)
        logging.info('All WKT graphs will be written to %s', args.outputDir)        

    else:
        for dirpath, dirnames, files in os.walk(args.outputDir):
            if files:
                logging.error('%s already exists and is not empty', args.outputDir)
                exit(2)
            else:
                logging.info('All WKT graphs will be written to %s', args.outputDir)

    empty_line = re.compile('^ *$')
    with open(args.input) as infile:
        for line in infile:
            if empty_line.match(line):
                continue
            all_geometries.append(wkt.loads(line))

    G = nx.Graph()
    for geometry in all_geometries:
        if geometry['type'] in ['Point', 'LineString', 'MultiLineString']:
            add_geometry(geometry, G)

        elif geometry['type'] == 'GeometryCollection':
            for geom in geometry['geometries']:
                add_geometry(geom, G)

    logging.info('The graph has %d nodes and %d edges', G.number_of_nodes(),
                                                        G.number_of_edges())
    components = connected_components(G)
    lComp = components[0]
    logging.info('The largest connected component has %d nodes and %d edges', lComp.number_of_nodes(), lComp.number_of_edges())
    write_all_graphs(args.outputDir, components)


def write_all_graphs(outputDir, graphList):
    write_graph(outputDir + 'largest_component.wkt', graphList[0])
    index = 0
    for graph in graphList[1]:
        graphFile = '{0}subgraph_{1}'.format(outputDir, index)
        write_graph(graphFile, graph)
        index += 1


def write_graph(filename, graph):
    with open(filename, 'wb') as out:
        for edge in graph.edges():
            out.write(graph[edge[0]][edge[1]]['wkt'])
            out.write('\n')


def add_geometry(geometry, graph):
    if geometry['type'] == 'Point':
        x = geometry['coordinates'][0]
        y = geometry['coordinates'][1]
        create_node_from_point(x, y, graph)

    elif geometry['type'] == 'LineString':
        create_nodes_from_line(geometry['coordinates'], graph)

    elif geometry['type'] == 'MultiLineString':
            print('MULTILINE')


def create_node_from_point(x, y, graph):
    coords = (x, y)
    graph.add_node(coords)


def create_nodes_from_line(pointlist, graph):
    previous_point = ()
    for point in pointlist:
        current_point = (point[0], point[1])
        create_node_from_point(point[0], point[1], graph)
        if len(previous_point) > 0:
            edge_wkt = 'LINESTRING ({0} {1}, {2} {3})'.format(
                previous_point[0], previous_point[1],
                current_point[0], current_point[1])

            graph.add_edge(previous_point, current_point,
                           attr_dict={'wkt': edge_wkt})

        previous_point = (point[0], point[1])


def connected_components(G):
    subgraphs = list(nx.connected_component_subgraphs(G, copy=True))
    comp = max(nx.connected_component_subgraphs(G), key=len)
    logging.info('There\'s %d connected subgraphs', len(subgraphs))
    logging.info('Largest component has %d nodes', comp.number_of_nodes())

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
    return [largest_component, subgraphs]


if __name__ == '__main__':
    main()
