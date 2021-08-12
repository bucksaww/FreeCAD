# -*- coding: utf-8 -*-
# ***************************************************************************
# *   Copyright (c) 2021 sliptonic shopinthewoods@gmail.com                 *
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


__title__ = "Path Target Shape DocObject creation"
__author__ = "sliptonic (Brad Collette)"
__url__ = "http://www.freecadweb.org"
__doc__ = "functions to create shape document objects"

from Shapes import TargetShape
import FreeCAD


def makeSpotShape(doc, name="SpotShape"):
    """
    makeSpotShape(document, [name]):
    makes a Path drilling-like target shape
    """
    from Shapes import SpotShape

    obj = doc.addObject("Part::FeaturePython", name)
    SpotShape.SpotShape(obj)
    if FreeCAD.GuiUp:
        TargetShape.ViewProviderTargetShape(obj.ViewObject)
    return obj


def makeLineFollowingShape(doc, name="LineFollowingShape"):
    """
    makeLineFollowingShape(document, [name]):
    makes a Path profile-like target shape
    """
    from Shapes import LineFollowingShape

    obj = doc.addObject("Part::FeaturePython", name)
    LineFollowingShape.LineFollowingShape(obj)
    if FreeCAD.GuiUp:
        TargetShape.ViewProviderTargetShape(obj.ViewObject)
    return obj


def makeVolumeClearingShape(doc, name="VolumeClearingShape"):
    """
    makeVolumeClearingShape(document, [name]):
    makes a Path pocket-like target shape
    """
    from Shapes import VolumeClearingShape

    obj = doc.addObject("Part::FeaturePython", name)
    VolumeClearingShape.VolumeClearingShape(obj)
    if FreeCAD.GuiUp:
        TargetShape.ViewProviderTargetShape(obj.ViewObject)
    return obj


def makeTargetGroup(doc, name="TargetGroup"):
    """
    makeTargetGroup(document, [name]):
    makes a Path target group. target groups allow managing
    sets of targetshapes with identical properties.
    """

    obj = doc.addObject("Part::FeaturePython", name)
    TargetShape.TargetGroup(obj)
    if FreeCAD.GuiUp:
        TargetShape.ViewProvider_TargetGroup(obj.ViewObject)
    return obj
