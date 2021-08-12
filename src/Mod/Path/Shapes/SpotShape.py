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
import Part
import PathScripts.PathLog as PathLog
import Shapes.TargetShape as TargetShape
import numpy


__title__ = "SpotShape Implementation"
__author__ = "sliptonic (Brad Collette)"
__url__ = "http://www.freecadweb.org"
__doc__ = "Classes and implementation for drilling-like target shapes"

if True:
    PathLog.setLevel(PathLog.Level.DEBUG, PathLog.thisModule())
    PathLog.trackModule(PathLog.thisModule())
else:
    PathLog.setLevel(PathLog.Level.INFO, PathLog.thisModule())


def translate(context, text, disambig=None):
    return QtCore.QCoreApplication.translate(context, text, disambig)


class SpotShape(TargetShape.TargetShape):
    def getShape(self, obj):
        """ returns a tuple of an edge and diameter for the target
        (edge, diameter)
        """
        super().getShape(obj)

        v1 = obj.Shape.Edges[2].Curve.Center
        v2 = obj.Shape.Edges[0].Curve.Center
        diam = obj.Shape.Edges[2].Curve.Radius * 2
        return (Part.makeLine(v1, v2), diam)


    def initShapeProperties(self, obj):
        obj.addProperty(
            "App::PropertyLinkSubGlobal",
            "Base",
            "Path",
            QtCore.QT_TRANSLATE_NOOP("PathOp", "The base geometry for this operation"),
        )
        obj.addProperty(
            "App::PropertyBool",
            "Reverse",
            "Path",
            QtCore.QT_TRANSLATE_NOOP("PathOp", "Reverse the direction of the feature"),
        )
        obj.setEditorMode("Reverse", 2)  # Only thru-hole features can be reversed

        obj.Reverse = False

    def execute(self, obj):
        if obj.Base is None:
            return

        self.__makeShape(obj)

    def __makeShape(self, obj):
        """
        takes a tuple(obj, subelement) and creates a cylindrical shape
        corresponding to the area removed by an ideal spot operation.
        Do not trust the cylinder Vertex ordering. Rather find the seam and
        use the vertex ordering of it to determine directionality.
        """

        def makeStockLine(holeAxis):
            """
            The stockline is an edge running through the axis of a drilling
            target and terminating at the intersection of the stock at both ends.
            Assumes a holeAxis is a Part.Line
            """

            return holeAxis.common(obj.Stock.Shape).Edges[0]

        def line_plane_intersection(edge, face):
            """Returns the vertex that is at the intersection of the face
            and the edge"""

            edge = edge.Edges[0]
            inter = face.Surface.intersect(edge.Curve)[0][0].toShape().Point
            return inter

        def checkForBlindHole(baseshape, selectedFace):
            """
            check for blind holes, returns the bottom face if found, none
            if the hole is a thru-hole
            """
            circularFaces = [
                f
                for f in baseshape.Faces
                if len(f.OuterWire.Edges) == 1
                and type(f.OuterWire.Edges[0].Curve) == Part.Circle
            ]

            circularFaceEdges = [f.OuterWire.Edges[0] for f in circularFaces]
            commonedges = [
                i for i in selectedFace.Edges for x in circularFaceEdges if i.isSame(x)
            ]

            bottomface = None
            for f in circularFaces:
                for e in f.Edges:
                    for i in commonedges:
                        if e.isSame(i):
                            bottomface = f
                        break

            if bottomface is None:
                obj.setEditorMode("Reverse", 0)
            else:
                obj.Reverse = False
                obj.setEditorMode("Reverse", 2)

            return bottomface

        def makeBlindDrill(stockline, bottomFace):
            """
            finds the intersection point. constructs a line from ipoint to
            vertices of stockline and compares direction to return the part on the
            normal positive side of the face
            """
            ipoint = line_plane_intersection(stockline, bottomFace)
            norm = bottomFace.Faces[0].normalAt(0, 0)

            for v in stockline.Vertexes:
                _templine = Part.makeLine(v.Point, ipoint)
                includedAngle = _templine.Curve.Direction.getAngle(norm.negative())

                if numpy.isclose(includedAngle, 0, rtol=1e-05, atol=1e-06):
                    return _templine

            return None

        def cylinderElements(cyl):
            """takes a cylindrical face and return a dictionary of the
            component elements:
            center1 - center of lid1
            center2 - center of lid2
            seam
            axis
            radius
            """
            result = {}
            lidnum = 1
            for e in cyl.Edges:
                if isinstance(e.Curve, Part.Line):  # found the seam
                    result["seam"] = e
                elif type(e.Curve) in [
                    Part.Circle,
                    Part.Ellipse,
                ]:  # Regular circular face
                    result["center{}".format(lidnum)] = e.Curve.Center
                    lidnum += 1
            result["axis"] = cyl.Surface.Axis
            result["radius"] = cyl.Surface.Radius
            return result

        docObj = obj.Base[0]
        subObj = docObj.getSubObject(obj.Base[1][0])

        if subObj.ShapeType == "Face" and str(subObj.Surface) == "<Cylinder object>":
            cylElements = cylinderElements(subObj)

            if obj.Reverse:
                v1 = cylElements["center1"]
                v2 = cylElements["center2"]
                featureTop = v1
            else:
                v1 = cylElements["center2"]
                v2 = cylElements["center1"]
                featureTop = v2

            holeAxis = Part.Line(
                v1, v2
            ).toShape()  # infinite line through the cylindrical hole feature
            stockline = makeStockLine(holeAxis)

            bottomFace = checkForBlindHole(docObj.Shape, subObj)

            if bottomFace is None:
                referenceLine = stockline
            else:
                referenceLine = makeBlindDrill(stockline, bottomFace)

            radius = cylElements["radius"]

        else:
            if subObj.ShapeType == "Face":
                if len(subObj.Edges) == 1:  # circular face
                    edge = subObj.Edges[0]
                elif len(subObj.Edges) == 2:  # mmmm donuts!
                    e1 = subObj.Edges[0]
                    e2 = subObj.Edges[1]
                    edge = e1 if e1.Curve.Radius < e2.Curve.Radius else e2

            else:  # simple edge
                edge = subObj.Edges[0]

            axis = edge.Curve.Axis

            v1 = edge.Curve.Center  # cylinder center
            v2 = v1.add(axis)
            holeAxis = Part.Line(
                v2, v1
            ).toShape()  # infinite line through the cylindrical hole feature
            stockline = makeStockLine(holeAxis)

            # Figure out which piece of the stockline we want to retain
            dist = v2.distanceToLineSegment(v1, stockline.Vertexes[0].Point).Length
            if numpy.isclose(dist, 0, rtol=1e-05, atol=1e-06):
                referenceLine = Part.makeLine(stockline.Vertexes[0].Point, v1)
            else:
                referenceLine = Part.makeLine(stockline.Vertexes[1].Point, v1)

            radius = edge.Curve.Radius
            featureTop = edge.Curve.Center

        if obj.Begin == "Feature":
            referenceLine = Part.makeLine(featureTop, referenceLine.Vertexes[1].Point)

        # Apply the customizations

        r1 = referenceLine.Vertexes[0].Point
        r2 = referenceLine.Vertexes[1].Point

        # offsetting the beginning position
        if obj.BeginOffset != 0.0:
            v1_dir = r1.sub(r2).normalize()
            v1_dir.multiply(obj.BeginOffset.Value)
            v1_new = r1.add(v1_dir)
            referenceLine = Part.makeLine(v1_new, r2)

        # Explicit length setting
        if obj.End == "Length":
            length = obj.Length.Value
        else:
            length = referenceLine.Length
            obj.Length = length

        # construct the result
        cyl = Part.makeCylinder(
            radius,
            length,
            referenceLine.Vertexes[0].Point,
            referenceLine.Curve.Direction,
        )

        obj.Shape = cyl
