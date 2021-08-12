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

__title__ = "VolumeClearingShape Implementation"
__author__ = "sliptonic (Brad Collette)"
__url__ = "http://www.freecadweb.org"
__doc__ = "Classes and implementation for pocket-like target shapes"

if False:
    PathLog.setLevel(PathLog.Level.DEBUG, PathLog.thisModule())
    PathLog.trackModule(PathLog.thisModule())
else:
    PathLog.setLevel(PathLog.Level.INFO, PathLog.thisModule())


def translate(context, text, disambig=None):
    return QtCore.QCoreApplication.translate(context, text, disambig)


class VolumeClearingShape(TargetShape.TargetShape):
    def initShapeProperties(self, obj):
        obj.addProperty(
            "App::PropertyLinkSubGlobal",
            "Base",
            "Path",
            QtCore.QT_TRANSLATE_NOOP(
                "PathShape", "The base geometry for this operation"
            ),
        )
        obj.addProperty(
            "App::PropertyVectorDistance",
            "ExtrusionVector",
            "Path",
            QtCore.QT_TRANSLATE_NOOP(
                "PathShape", "The vector and distance of subshape extrusion"
            ),
        )
        obj.addProperty(
            "App::PropertyEnumeration",
            "ReferenceDirection",
            "Path",
            QtCore.QT_TRANSLATE_NOOP(
                "PathPocket", "Indicates the directionality (up) of the shape"
            ),
        )
        obj.ReferenceDirection = ["Z axis", "Face Normal"]
        obj.ExtrusionVector = App.Vector(0, 0, 1)

    def execute(self, obj):
        if obj.Base is None:
            return

        if obj.ReferenceDirection == 'Face Normal':
            docObj = obj.Base[0]
            subObjs = [docObj.getSubObject(o) for o in obj.Base[1]]
            face = subObjs[0]
            obj.ExtrusionVector = face.normalAt(0,0)
        else:
            obj.ExtrusionVector = App.Vector(0, 0, 1)

        self.__makeShape(obj)

    def __makeShape(self, obj):
        def buildprojection(shape):
            outline = TechDraw.findShapeOutline(shape, 1, obj.ExtrusionVector)
            Part.show(outline, "outline")
            return Part.makeFace(outline, "Part::FaceMakerSimple")

        def selToBoundShape(shape, extension=1.0):
            print("extension", extension)
            bb = shape.BoundBox
            lenX = bb.XLength + extension
            lenY = bb.YLength + extension
            p1 = App.Vector(bb.Center.x - lenX / 2, bb.Center.y - lenY / 2, 0)
            p2 = App.Vector(bb.Center.x - lenX / 2, bb.Center.y + lenY / 2, 0)
            p3 = App.Vector(bb.Center.x + lenX / 2, bb.Center.y + lenY / 2, 0)
            p4 = App.Vector(bb.Center.x + lenX / 2, bb.Center.y - lenY / 2, 0)
            poly = Part.makePolygon([p1, p2, p3, p4, p1])
            return Part.makeFace(poly, "Part::FaceMakerSimple")

        def negativePart(shp):
            """
            make a target shape by subtracting the base from the stock
            """
            return obj.Stock.Shape.cut(shp)

        docObj = obj.Base[0]
        subObjs = [docObj.getSubObject(o) for o in obj.Base[1]]

        if len(subObjs) == 0:  # a single solid
            obj.Shape = negativePart(docObj.Shape)

        elif len(subObjs) == 1:  # 1 face
            outerwire = subObjs[0].OuterWire
            face = Part.makeFace(outerwire, "Part::FaceMakerSimple")
            shp = face.extrude(
                obj.ExtrusionVector.multiply(obj.Stock.Shape.BoundBox.DiagonalLength)
            )
            obj.Shape = obj.Stock.Shape.common(shp)

        else:
            subbb = Part.makeCompound(subObjs)
            outline = buildprojection(docObj.Shape)
            newface = selToBoundShape(subbb, 12)

            obj.Shape = newface.cut(outline).extrude(
                App.Vector(0, 0, docObj.Shape.BoundBox.ZLength)
            )

    def getShape(self, obj):
        super().getShape(obj)
