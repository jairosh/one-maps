#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: Jairo Sanchez
# @Date:   2017-03-15 11:55:46
# @Last Modified by:   Jairo Sanchez
# @Last Modified time: 2017-03-22 00:35:44
import pyproj
from geomet import wkt
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--projection',
                        help='Data original projection',
                        type=str,
                        default='epsg:4326')
    parser.add_argument('-i', '--input',
                        type=str,
                        help='Input WKT file',
                        required=True)
    parser.add_argument('-o', '--output',
                        help='Output WKT file',
                        type=str,
                        default='./output_reprojected.wkt')
    args = parser.parse_args()

    newStr = ''
    with open(args.input, 'rb') as wktin:
        line_number = 0
        for line in wktin:
            try:
                newStr += reproject_wkt_entity(line, args.projection)
                newStr += '\n'
            except ValueError:
                print 'Error processing line {0} in {1}'.format(line_number,
                                                                args.input)
                raise

            line_number += 1

    with open(args.output, 'wb') as out:
        out.write(newStr)


def reproject_single_point(x, y, srcProj):
    dstProj = pyproj.Proj(init='epsg:3857', preserve_units=True)
    return pyproj.transform(srcProj, dstProj, x, y)


def reproject_wkt_entity(entity, projection):
    if entity is '' or entity.rstrip() is '':
        return ''

    srcProj = pyproj.Proj(init=projection, preserve_units=True)

    json = wkt.loads(entity)
    if json['type'] is 'Point':
        origin = json['coordinates']
        x_1, y_1 = reproject_single_point(origin[0], origin[1], srcProj)
        new_entitiy = 'POINT ({0} {1})'
        return new_entitiy.format(x_1, y_1)

    elif json['type'] is 'LineString':
        newLine = 'LINESTRING ('
        initial_char = ''
        for point in json['coordinates']:
            newX, newY = reproject_single_point(point[0], point[1], srcProj)
            fmt = '{} {}'
            newLine += initial_char + fmt.format(newX, newY)
            initial_char = ', '

        return newLine + ')'

    elif json['type'] is 'MultiLineString':
        multiline = 'MULTILINESTRING ('
        initial_char = ''
        for line in json['coordinates']:
            newLine = '('
            line_initial_char = ''
            for point in line:
                nX, nY = reproject_single_point(point[0], point[1], srcProj)
                fmt = '{} {}'
                newLine += line_initial_char + fmt.format(nX, nY)
                line_initial_char = ', '

            multiline += initial_char + newLine + ')'
            initial_char = ', '

        return multiline + ')'

    elif json['type'] is 'Polygon':
        print 'POLYGON'

    print 'NONE'
    print json
    return ''


if __name__ == '__main__':
    main()
