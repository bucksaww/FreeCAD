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

__title__ = "AreaClearingShape Implementation"
__author__ = "sliptonic (Brad Collette)"
__url__ = "http://www.freecadweb.org"
__doc__ = "Classes and implementation for engrave-like target shapes"

if False:
    PathLog.setLevel(PathLog.Level.DEBUG, PathLog.thisModule())
    PathLog.trackModule(PathLog.thisModule())
else:
    PathLog.setLevel(PathLog.Level.INFO, PathLog.thisModule())


def translate(context, text, disambig=None):
    return QtCore.QCoreApplication.translate(context, text, disambig)


class AreaClearingShape(TargetShape.TargetShape):
    def initShapeProperties(self, obj):
        obj.addProperty(
            "App::PropertyLinkSubGlobal",
            "Base",
            "Path",
            QtCore.QT_TRANSLATE_NOOP("PathOp", "The base geometry for this operation"),
        )

    def onChanged(self, obj, prop):
        if prop == "Base":
            if obj.Base is None:
                return

            # 0 subobjects is an error
            if len(obj.Base[1]) == 0:
                raise ValueError

            docObj = obj.Base[0]
            referenceFace = docObj.getSubObject(obj.Base[1][0])
            obj.AlignmentVector = referenceFace.normalAt(0,0)

            # One subobject is valid
            if len(obj.Base[1]) == 1:
                return

            # Multiple subobjects may be valid. Check for coplanarity
            else:
                coplanars = [obj.Base[1][0]]
                for sub in obj.Base[1][1:]:
                    face = docObj.getSubObject(sub)
                    if referenceFace.isCoplanar(face):
                        coplanars.append(sub)
                if len(coplanars) != len(obj.Base[1]):
                    obj.Base = (docObj, coplanars)

    def execute(self, obj):
        if obj.Base is None:
            return

        self.__makeShape(obj)

    def __makeShape(self, obj):

        docObj = obj.Base[0]
        subObjs = [docObj.getSubObject(o) for o in obj.Base[1]]

        if len(subObjs) == 0:  # a single solid
            pass

        else:
            sec = Part.makeCompound(subObjs)
            obj.Shape = sec.copy()  # shapePerimeter(sec)

    def getShape(self, obj):
        super().getShape(obj)
