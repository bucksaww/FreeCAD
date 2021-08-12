# -*- coding: utf-8 -*-
# ***************************************************************************
# *   Copyright (c) 2021 sliptonic <shopinthewoods@gmail.com>               *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

"""
This module contains functions and utilities to assist with rotating and positioning
objects for multi-axis CNC operations.
"""

import FreeCAD
import PathScripts.PathLog as PathLog
import math

__title__ = "PathRotation"
__author__ = "sliptonic (Brad Collette)"
__url__ = "http://www.freecadweb.org"
__doc__ = "helper functions for rotating shapes for multi-axis milling"

if False:
    PathLog.setLevel(PathLog.Level.DEBUG, PathLog.thisModule())
    PathLog.trackModule(PathLog.thisModule())
else:
    PathLog.setLevel(PathLog.Level.INFO, PathLog.thisModule())


def getFaceName(shp, targetface):
    for idx, face in enumerate(shp.Faces):
        if face.hashCode() == targetface.hashCode():
            return "Face{}".format(idx + 1)


def __getCRotation(facenorm, aMin, aMax):
    """
    Calculate the C axis rotation component.
    multiple poses may be possible depending on how the A axis is allowed to
    move.
    """

    posRot = negRot = None
    facenorm.projectToPlane(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1))

    if aMax > 0:
        posRot = facenorm.getAngle(FreeCAD.Vector(0, 1, 0))
        posRot = math.degrees(posRot) if not math.isnan(posRot) else 0

    if aMin < 0:
        negRot = facenorm.getAngle(FreeCAD.Vector(0, -1, 0))
        negRot = math.degrees(negRot) if not math.isnan(negRot) else 0

    PathLog.debug("pos: {} neg: {}".format(posRot, negRot))
    if posRot is not None and negRot is not None:
        # if both allowed, choose shortest
        cRot = 0 - negRot if negRot < posRot else posRot
    elif posRot is not None:
        cRot = posRot
    elif negRot is not None:
        cRot = 0 - negRot
    else:
        raise ValueError
    PathLog.track("Returning CRot: {}".format(cRot))
    return cRot


def __getARotation(facenorm, aMin, aMax):
    """
    Calculate the A axis rotation component.
    Final rotation is always assumed to be around +X. The sign of the returned
    value indicates direction of rotation.

    """

    aRot = facenorm.getAngle(FreeCAD.Vector(0, 0, 1))
    aRot = math.degrees(aRot) if not math.isnan(aRot) else 0

    align = facenorm.getAngle(FreeCAD.Vector(0, 1, 0))
    align = math.degrees(align) if not math.isnan(align) else 0

    if math.isnan(align):

        aRot = 0
    else:
        if align > 90:
            aRot = 0 - aRot if aRot > 0 else aRot

        if align < 90:
            aRot = 0 - aRot if aRot < 0 else aRot

    PathLog.track('facenorm {}, aRot {}, align {}, aMin {}, aMax{}'.format(facenorm, aRot, align, aMin, aMax))
    if aRot < aMin or aRot > aMax:
        raise ValueError("The calculated A rotation exceeds the allowed range")

    return aRot

def setRotationForEdgeCA(originaledge, aMin=0, aMax=90):
    """
    Calculates independent C an A axis rotations to rotate an edge to align
    with the positive Z axis.

    It first rotates the object around the Z axis (C rotation)
    to align the edge with the positive Y axis. Then around the X axis
    (A rotation) to align with Z.

    The min and max arguments dictate the range of motion allowed in the A axis.
    It is assumed the C axis is continous rotation and A rotates up
    to 90 degrees in the positive direction.

    Neither the referenceFace or shape are affected by this function.

    returns the axis rotations and a new placement.

    {'A':aRot, 'C':cRot},  newPlacement
    """

    import Part
    edge = originaledge.copy()
    v0 = edge.Vertexes[0].Point
    v1 = edge.Vertexes[1].Point
    edgenorm = v0.sub(v1) #.normalize()
    PathLog.track("v0 {} v1 {}".format(v0, v1))

    cRot = __getCRotation(edgenorm, aMin, aMax)
    PathLog.track("Rotating C {} degrees".format(cRot))

    # rotate the shape around Z
    __oneRotation(edge, FreeCAD.Vector(0, 0, 1), cRot)

    v0 = edge.Vertexes[0].Point
    v1 = edge.Vertexes[1].Point
    edgenorm = v0.sub(v1) #.normalize()

    aRot = __getARotation(edgenorm, aMin, aMax)
    PathLog.track("Rotating A {} degrees".format(aRot))

    __oneRotation(edge, FreeCAD.Vector(1, 0, 0), aRot)

    # FreeCAD.ActiveDocument.recompute()

    return {"A": aRot, "C": cRot}, edge

def setRotationCA(referenceFace, origshape, aMin=0, aMax=90):
    PathLog.track()
    """
    Calculates independent C an A axis rotations to rotate a shape to align
    the face normal with the positive Z axis.

    It first rotates the object around the Z axis (C rotation)
    to align the face normal with the positive Y axis. Then around the X axis
    (A rotation).

    The min and max arguments dictate the range of motion allowed in the A axis.
    It is assumed the C axis is continous rotation and A rotates up
    to 90 degrees in the positive direction.

    Neither the referenceFace or shape are affected by this function.

    returns the axis rotations and new placment.
    {'A':aRot, 'C':cRot},  newPlacement

    """

    shape = origshape.copy()
    facename = getFaceName(origshape, referenceFace)
    face = getattr(shape, facename)

    # Calculate C rotation
    facenormal = face.normalAt(0, 0)
    cRot = __getCRotation(facenormal, aMin, aMax)
    PathLog.debug("Rotating C {} degrees".format(cRot))

    # rotate the shape around Z
    __oneRotation(shape, FreeCAD.Vector(0, 0, 1), cRot)

    # calculate A rotation
    face = getattr(shape, facename)
    facenormal = face.normalAt(0, 0)
    aRot = __getARotation(facenormal)
    PathLog.debug("Rotating A {} degrees".format(aRot))

    __oneRotation(shape, FreeCAD.Vector(1, 0, 0), aRot)

    import Part

    Part.show(shape)
    FreeCAD.ActiveDocument.recompute()

    return {"A": aRot, "C": cRot}, shape.Placement


def __oneRotation(obj, vec, angle):
    """
    rotates an object around one machine axis. return the new shape
    placement
    """

    if angle == 0:
        return
    center = FreeCAD.Vector(0, 0, 0)
    # ci = obj.getGlobalPlacement().inverse().multVec(center)
    ci = obj.Placement.inverse().multVec(center)
    real_center = obj.Placement.multVec(ci)

    shape = obj.copy()
    shape.rotate(real_center, vec, angle)

    obj.Placement = shape.Placement


def __calculateRotationPlacement(face, shape):
    """
    given a reference face and a shape, calculate the new placement for the
    shape to align the face normal with the positive Z axis. This is
    a direct move rather than independent axis moves
    """

    PathLog.track(face)
    facenormal = face.normalAt(0, 0)

    axis = facenormal.cross(FreeCAD.Vector(0, 0, 1))
    if axis.Length > 0 and axis.Length < 1:
        axis = axis.normalize()
        angle = facenormal.getAngle(FreeCAD.Vector(0, 0, 1)) * 180 / math.pi
        newplace = shape.Placement.multiply(
            FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), axis, angle)
        )
        return newplace
    raise Exception("Something unforseen happend PathRotation 199")
