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


from PySide import QtCore
import FreeCAD as App
import Part
import PathScripts.PathLog as PathLog
import Shapes.TargetShape as TargetShape
import TechDraw as TechDraw

__title__ = "LineFollowShape Implementation"
__author__ = "sliptonic (Brad Collette)"
__url__ = "http://www.freecadweb.org"
__doc__ = "Classes and implementation for profile-like target shapes"

if False:
    PathLog.setLevel(PathLog.Level.DEBUG, PathLog.thisModule())
    PathLog.trackModule(PathLog.thisModule())
else:
    PathLog.setLevel(PathLog.Level.INFO, PathLog.thisModule())


def translate(context, text, disambig=None):
    return QtCore.QCoreApplication.translate(context, text, disambig)


class LineFollowingShape(TargetShape.TargetShape):
    def initShapeProperties(self, obj):
        obj.addProperty(
            "App::PropertyLinkSubGlobal",
            "Base",
            "Path",
            QtCore.QT_TRANSLATE_NOOP("PathOp", "The base geometry for this operation"),
        )

    def execute(self, obj):
        if obj.Base is None:
            return

        self.__makeShape(obj)

    def __makeShape(self, obj):
        def shapePerimeter(shp):
            """
            produces a perimeter for the whole shape
            """

            if obj.Begin == "Stock":
                zTop = obj.Stock.Shape.BoundBox.ZMax
            elif obj.Begin == "Feature":
                zTop = shp.BoundBox.ZMax

            zTop += obj.BeginOffset.Value

            outline = TechDraw.findShapeOutline(shp, 1, App.Vector(0, 0, 1))
            newPlace = App.Placement(App.Vector(0, 0, zTop), outline.Placement.Rotation)
            outline.Placement = newPlace

            if obj.End == "Stock":
                height = zTop - obj.Stock.Shape.BoundBox.ZMin
            elif obj.End == "Feature":
                height = zTop - shp.BoundBox.ZMin
            else:
                # Explicit length setting
                height = obj.Length.Value

            obj.Length = height
            height = 0 - height  # reverse the direction
            print("height", height)
            face = outline.extrude(App.Vector(0, 0, height))
            return face

        docObj = obj.Base[0]
        subObjs = [docObj.getSubObject(o) for o in obj.Base[1]]

        if len(subObjs) == 0:  # a single solid
            obj.Shape = shapePerimeter(docObj.Shape)

        else:
            sec = Part.makeCompound(subObjs)
            obj.Shape = shapePerimeter(sec)

    def getShape(self, obj):
        super().getShape(obj)
