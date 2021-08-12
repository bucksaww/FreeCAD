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
from abc import ABC, abstractmethod
import PathScripts.PathLog as PathLog

__title__ = "TargetShape Base Classes"
__author__ = "sliptonic (Brad Collette)"
__url__ = "http://www.freecadweb.org"
__doc__ = "Base Classes for all Target Shapes"


if False:
    PathLog.setLevel(PathLog.Level.DEBUG, PathLog.thisModule())
    PathLog.trackModule(PathLog.thisModule())
else:
    PathLog.setLevel(PathLog.Level.INFO, PathLog.thisModule())


def translate(context, text, disambig=None):
    return QtCore.QCoreApplication.translate(context, text, disambig)


class ViewProviderTargetShape:
    def __init__(self, vobj):
        vobj.Proxy = self
        vobj.Transparency = 80
        vobj.ShapeColor = (1.0000, 0.3333, 1.0000)
        vobj.Selectable = False

    def __getstate__(self):
        return None

    def __setstate__(self, _state):
        return None


class TargetShape(ABC):
    def __init__(self, obj):
        obj.addProperty(
            "App::PropertyString",
            "UserLabel",
            "Base",
            QtCore.QT_TRANSLATE_NOOP("Path", "User Assigned Label"),
        )
        obj.addProperty(
            "App::PropertyLink",
            "Stock",
            "Base",
            QtCore.QT_TRANSLATE_NOOP("Path", "Solid object to be used as stock."),
        )

        obj.addProperty(
            "App::PropertyEnumeration",
            "Begin",
            "Depths",
            QtCore.QT_TRANSLATE_NOOP("Path", "start depth for target shape"),
        )
        obj.addProperty(
            "App::PropertyDistance",
            "BeginOffset",
            "Depths",
            QtCore.QT_TRANSLATE_NOOP("Path", "Offset distance"),
        )
        obj.addProperty(
            "App::PropertyEnumeration",
            "End",
            "Depths",
            QtCore.QT_TRANSLATE_NOOP("Path", "end depth for target shape"),
        )
        obj.addProperty(
            "App::PropertyDistance",
            "Length",
            "Depths",
            QtCore.QT_TRANSLATE_NOOP("Path", "Distance from start point"),
        )
        obj.addProperty(
            "App::PropertyBool",
            "Active",
            "Path",
            QtCore.QT_TRANSLATE_NOOP(
                "PathOp", "Make False, to prevent operation from generating code"),
            )
        obj.addProperty(
            "App::PropertyVectorDistance",
            "AlignmentVector",
            "Path",
            QtCore.QT_TRANSLATE_NOOP(
                "PathShape", "This vector establishes local 'up' for the target shape"
            ),
        )
        obj.Begin = ["Stock", "Feature"]
        obj.Begin = "Stock"

        obj.End = ["Stock", "Length", "Feature"]
        obj.End = "Stock"

        obj.Active = True

        obj.setEditorMode("Length", 2)

        self.initShapeProperties(obj)
        obj.Proxy = self

    def onChanged(self, obj, prop):
        """Do something when a property has changed"""
        if prop == "End":
            if obj.End == "Length":
                obj.setEditorMode("Length", 0)
            else:
                obj.setEditorMode("Length", 2)

    @abstractmethod
    def getShape(self, obj):
        pass

    @abstractmethod
    def execute(self, obj):
        pass


class ViewProvider_TargetGroup:
    def __init__(self, vobj):
        vobj.Proxy = self
        vobj.addExtension("Gui::ViewProviderGroupExtensionPython")


class TargetGroup(TargetShape):
    def __init__(self, obj):
        super().__init__(obj)
        obj.Proxy = self
        obj.addExtension("App::GroupExtensionPython")

    def initShapeProperties(self, obj):
        obj.removeProperty("Stock")

    def getShape(self, obj):
        pass

    def onChanged(self, obj, prop):
        super().onChanged(obj, prop)
        managedprops = ["Begin", "BeginOffset", "End", "Length"]

        if prop == "Proxy":
            return

        if prop in managedprops:
            val = obj.getPropertyByName(prop)
            for child in obj.Group:
                if hasattr(child, prop):
                    setattr(child, prop, val)
            return

        # if prop == 'Group':
        #     for p in managedprops:

    def addObject(self, obj):
        print("inaddobj")
        print(obj)

    def execute(self, obj):
        pass
