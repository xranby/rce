#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       ROS.py
#       
#       Copyright 2011 dominique hunziker <dominique.hunziker@gmail.com>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
#       
#       

########################################################################
### Imports
########################################################################

import re
import os
import sys

########################################################################
### Adjust the (ROS) environment here
########################################################################

# Custom path for ROS packages
_SOURCE_FOR_CUSTOM_PACKAGES = '/home/dominique/ROS'

# Default ROS configuration
_EXPORTS = [('PYTHONPATH', '/opt/ros/fuerte/lib/python2.7/dist-packages'),
            ('PATH', '/opt/ros/fuerte/bin{0}$PATH'.format(os.pathsep)),
            ('CMAKE_PREFIX_PATH', '/opt/ros/fuerte/share/catkin/cmake/Modules{0}/opt/ros/fuerte{0}$CMAKE_PREFIX_PATH'.format(os.pathsep)),
            ('LD_LIBRARY_PATH', '/opt/ros/fuerte/lib{0}$LD_LIBRARY_PATH'.format(os.pathsep)),
            ('PKG_CONFIG_PATH', '/opt/ros/fuerte/lib/pkgconfig{0}$PKG_CONFIG_PATH'.format(os.pathsep)),
            ('ROS_ROOT', '/opt/ros/fuerte/share/ros'),
            ('ROS_PACKAGE_PATH', '{1}{0}/opt/ros/fuerte/share{0}/opt/ros/fuerte/stacks'.format(os.pathsep, _SOURCE_FOR_CUSTOM_PACKAGES)),
            ('ROS_MASTER_URI', 'http://localhost:11311'),
            ('ROS_ETC_DIR', '/opt/ros/fuerte/etc/ros'),
            ('ROS_DISTRO', 'fuerte')]

########################################################################
### Do not change below here
########################################################################

def _uniquify(pathList):
    """ Remove all duplicates from a list whilst keeping the ordering """
    newPathList = []

    for path in pathList:
        if path not in newPathList:
            newPathList.append(path)

    return newPathList

_regex = re.compile('\$(\w+)')

for (envVar, rawValue) in _EXPORTS:
    matches = _regex.finditer(rawValue)
    value = rawValue

    for match in matches:
        value = value.replace(match.group(), os.environ.get(match.group(1), ''))
        value = value.strip(os.pathsep)

    os.environ[envVar] = os.pathsep.join(_uniquify(value.split(os.pathsep)))
    
    # Special case for the PYTHONPATH variable:
    if envVar == 'PYTHONPATH':
        for path in value.split(os.pathsep):
            sys.path.append(path)

        sys.path = _uniquify(sys.path)

# Scrub old ROS bin dirs, to avoid accidentally finding the wrong executables
os.environ['PATH'] = os.pathsep.join([x for x in os.environ['PATH'].split(os.pathsep) if not any([d for d in ['cturtle', 'diamondback', 'electric', 'unstable'] if d in x])])

########################################################################