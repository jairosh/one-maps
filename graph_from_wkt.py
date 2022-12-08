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
import csv
import sys

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)s - %(message)s', level=logging.DEBUG)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input',
                        type=str,
                        help='Input WKT file')
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
    all_geometries = []
    if '.csv' in args.input:
        logging.info('Processing CSV file')
        all_geometries = handle_csv(args.input)
    elif '.wkt' in args.input:
        logging.info('Processing WKT file')
        all_geometries = handle_wkt(args.input)
    else:
        logging.error('Please add the extension to the file')
        exit(3)

    if len(all_geometries) == 0:
        logging.error('No geometries were found in file')
        exit(4)
 
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
    
    # bbox = get_bounding_box(components[-1])
    newC = shift_graph_to_origin(components[0], get_bounding_box(components[0]))
    bbox = get_bounding_box(newC)
    logging.info('bounding box: \n%s', bbox_as_wkt(bbox))
    write_graph(args.outputDir + '/shifted.wkt', newC)

    write_all_graphs(args.outputDir, components)


def handle_csv(fname):
    """Reads the contents of a CSV file as WKT. This files are generated by QGIS

    Args:
        fname (str): The path to the CSV file
    Returns:
        geometries (list): A list of all the parsed geometries
    """
    geometries = []
    with open(fname, 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        for row in reader:
            geometries.append(wkt.loads(row['WKT']))
    return geometries


def handle_wkt(fname):
    """Reads the contents of a WKT file, one geometry per line

    Args:
        fname (str): The path to the WKT file
    Returns:
        geometries (list): A list of all the parsed geometries
    """
    geometries = []
    empty_line = re.compile('^ *$')
    with open(args.input) as infile:
        for line in infile:
            if empty_line.match(line):
                continue
            geometries.append(wkt.loads(line))
    return geometries


def write_all_graphs(outputDir, graphList):
    """Saves the given graphs as their WKT representations

    Args:
        outputDir (str): Target directory to write the files
        graphList (list): A list of graphs 
    """
    # Write the largest component
    write_graph(outputDir + '_largest_component.wkt', graphList.pop(0))
    index = 1
    for graph in graphList:
        graphFile = '{0}component_{1}.wkt'.format(outputDir, index)
        write_graph(graphFile, graph)
        index += 1


def write_graph(filename, graph):
    """Writes a single graph into the given file

    Args:
        filename (str): Path of the file to write
        graph (networkx.Graph): The graph to write
    """
    logging.info('Writing graph at %s', filename)
    with open(filename, 'w') as out:
        for edge in graph.edges():            
            out.write(graph[edge[0]][edge[1]]['wkt'])
            out.write('\n')


def add_geometry(geometry, graph):
    """Append a geometry to a Graph, creating the corresponding nodes and edges.
    The WKT string is stored as attribute of that node/edge

    Args:
        geometry (dict): a GeoJSON dict describing the geometry to add
        graph (networkx.Graph): The Graph where the geometry will be appended
    """
    if geometry['type'] == 'Point':
        logging.debug("Point: ")
        x = geometry['coordinates'][0]
        y = geometry['coordinates'][1]
        create_node_from_point(x, y, graph)

    elif geometry['type'] == 'LineString':
        create_nodes_from_line(geometry['coordinates'], graph)

    elif geometry['type'] == 'MultiLineString':
            print('MULTILINE')


def create_node_from_point(x, y, graph):
    """Creates a node from a geographic point in the given graph

    Args:
        x (float): x coordinate of the point
        y (float): y coordinate of the point
        graph (networkx.Graph): the Graph in which to create the node
    """
    coords = (x, y)
    graph.add_node(coords)


def create_nodes_from_line(pointlist, graph):
    """Creates nodes and edges in graph from a geographic line. It can have multiple
    points.

    Args:
        pointlist (list): List of pairs of coordinates describing the line
        graph (networkx.Graph): The graph where the line will be appended
    """
    previous_point = ()
    for point in pointlist:
        current_point = (point[0], point[1])
        create_node_from_point(point[0], point[1], graph)
        if len(previous_point) > 0:
            edge_wkt = 'LINESTRING ({0} {1}, {2} {3})'.format(
                previous_point[0], previous_point[1],
                current_point[0], current_point[1])

            graph.add_edge(previous_point, current_point, wkt=edge_wkt)

        previous_point = (point[0], point[1])


def connected_components(G):
    """Detects the connected components in a graph 

    Args:
        G (A NetworkX Graph): The original graph to "split" into subgraphs

    Returns:
        list: A list of the subgraphs, ordered by its number of nodes
    """    
    subgraphs = [G.subgraph(c).copy() for c in sorted(nx.connected_components(G), key=len, reverse=True)]
    logging.info('There\'s %d connected subgraphs', len(subgraphs))
    logging.info('Largest component has %d nodes', subgraphs[0].number_of_nodes())
    return subgraphs


def get_bounding_box(G):
    """Obtains the bounding box of a graph representing geographic features

    Args:
        G (networkx.Graph): The input graph

    Returns:
        list: The list of tuples indicating the bounding box coordinates
    """
    box = [(0, 0), (0, 0)]
    x_lower = sys.maxsize
    y_lower = sys.maxsize
    x_high = -10000000000
    y_high = -10000000000
    for node in G:
        if node[0] < x_lower: x_lower = node[0]
        if node[1] < y_lower: y_lower = node[1]
        if node[0] > x_high: x_high = node[0]
        if node[1] > y_high: y_high = node[1]

    box = [(x_lower, y_lower), (x_high, y_high)]
    return box


def bbox_as_wkt(bbox):
    """Creates a WKT string representing a bounding box

    Args:
        bbox (list): The list of tuples with two ordinate pairs representing the 
        bounding box

    Returns:
        str: A Polygon feature in WKT 
    """
    x1, y1 = bbox[0]
    x2, y2 = bbox[1]
    return 'POLYGON (({} {}, {} {}, {} {}, {} {}))'.format(x1, y1,
                                                           x1, y2,
                                                           x2, y2,
                                                           x2, y1,
                                                           x1, y1)



def shift_graph_to_origin(G, bounding_box):
    """ONE Simulator can have troubles with negative coordinates so for safety we shift the 
    map so the bounding box it's on the first quadrant

    Args:
        G (networkx.Graph): The graph with the geographic features to shift.
    
    Returns:
        networkx.Graph: A copy of the passed graph but the nodes are shifted so they all
        have positive coordinates.
    """
    G1 = nx.Graph()
    #bbox = get_bounding_box(G)
    x_shift = bounding_box[0][0] 
    y_shift = bounding_box[0][1] 
    logging.debug('Minimal coordinates: %s', bounding_box[0])
    x_shift = -x_shift
    y_shift = -y_shift
    logging.debug('Shifting by: %f, %f', x_shift, y_shift)
    for edge in G.edges():
        u_x = edge[0][0] + x_shift
        u_y = edge[0][1] + y_shift
        v_x = edge[1][0] + x_shift
        v_y = edge[1][1] + y_shift
        edge_wkt = 'LINESTRING ({0} {1}, {2} {3})'.format(u_x, u_y, v_x, v_y)                        
        G1.add_edge((u_x, u_y), 
                    (v_x, v_y),
                    wkt=edge_wkt)     
    return G1

if __name__ == '__main__':
    main()

