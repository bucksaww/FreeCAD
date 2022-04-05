#  -*- coding: utf-8 -*-
# ***************************************************************************
# *   Copyright (c) 2017 LTS <SammelLothar@gmx.de> under LGPL               *
# *   Copyright (c) 2020-2021 Schildkroet                                   *
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

from __future__ import print_function

import FreeCAD
import FreeCADGui
import Path
import PathScripts.PathDressup as PathDressup
import PathScripts.PathGeom as PathGeom
import PathScripts.PathLog as PathLog
import PathScripts.PathUtils as PathUtils
import math
import copy

import Generators.leadin_generator as leadin_generator

import PathMachineState

from PathScripts.PathGeom import (
    CmdMoveRapid,
    CmdMoveStraight,
    CmdMoveArc,
)

__doc__ = """LeadInOut Dressup USE ROLL-ON ROLL-OFF to profile"""

from PySide.QtCore import QT_TRANSLATE_NOOP

from PathPythonGui.simple_edit_panel import SimpleEditPanel

translate = FreeCAD.Qt.translate

if True:
    PathLog.setLevel(PathLog.Level.DEBUG, PathLog.thisModule())
    PathLog.trackModule(PathLog.thisModule())
else:
    PathLog.setLevel(PathLog.Level.INFO, PathLog.thisModule())


movecommands = CmdMoveStraight + CmdMoveArc
# currLocation = {}

class ObjectDressup:
    def __init__(self, obj):
        lead_styles = [
            QT_TRANSLATE_NOOP("Path_DressupLeadInOut", "Arc"),
            QT_TRANSLATE_NOOP("Path_DressupLeadInOut", "Tangent"),
            QT_TRANSLATE_NOOP("Path_DressupLeadInOut", "Perpendicular"),
        ]
        self.obj = obj
        obj.addProperty(
            "App::PropertyLink",
            "Base",
            "Path",
            QT_TRANSLATE_NOOP("App::Property", "The base path to modify"),
        )
        obj.addProperty(
            "App::PropertyBool",
            "LeadIn",
            "Path",
            QT_TRANSLATE_NOOP("App::Property", "Calculate roll-on to path"),
        )
        obj.addProperty(
            "App::PropertyBool",
            "LeadOut",
            "Path",
            QT_TRANSLATE_NOOP("App::Property", "Calculate roll-off from path"),
        )
        obj.addProperty(
            "App::PropertyBool",
            "KeepToolDown",
            "Path",
            QT_TRANSLATE_NOOP("App::Property", "Keep the Tool Down in Path"),
        )
        # obj.addProperty(
        #     "App::PropertyBool",
        #     "UseMachineCRC",
        #     "Path",
        #     QT_TRANSLATE_NOOP(
        #         "App::Property",
        #         "Use Machine Cutter Radius Compensation /Tool Path Offset G41/G42",
        #     ),
        # )
        obj.addProperty(
            "App::PropertyDistance",
            "Length",
            "Path",
            QT_TRANSLATE_NOOP("App::Property", "Length or Radius of the approach"),
        )
        obj.addProperty(
            "App::PropertyEnumeration",
            "StyleOn",
            "Path",
            QT_TRANSLATE_NOOP("App::Property", "The Style of motion into the Path"),
        )
        obj.StyleOn = lead_styles
        obj.addProperty(
            "App::PropertyEnumeration",
            "StyleOff",
            "Path",
            QT_TRANSLATE_NOOP("App::Property", "The Style of motion out of the Path"),
        )
        obj.StyleOff = lead_styles
        obj.addProperty(
            "App::PropertyEnumeration",
            "RadiusCenter",
            "Path",
            QT_TRANSLATE_NOOP(
                "App::Property", "The Mode of Point Radiusoffset or Center"
            ),
        )
        obj.RadiusCenter = [
            QT_TRANSLATE_NOOP("Path_DressupLeadInOut", "Radius"),
            QT_TRANSLATE_NOOP("Path_DressupLeadInOut", "Center"),
        ]
        obj.Proxy = self
        obj.addProperty(
            "App::PropertyDistance",
            "ExtendLeadIn",
            "Path",
            QT_TRANSLATE_NOOP("App::Property", "Extends LeadIn distance"),
        )
        obj.addProperty(
            "App::PropertyDistance",
            "ExtendLeadOut",
            "Path",
            QT_TRANSLATE_NOOP("App::Property", "Extends LeadOut distance"),
        )
        obj.addProperty(
            "App::PropertyBool",
            "RapidPlunge",
            "Path",
            QT_TRANSLATE_NOOP("App::Property", "Perform plunges with G0"),
        )
        obj.addProperty(
            "App::PropertyBool",
            "IncludeLayers",
            "Path",
            QT_TRANSLATE_NOOP(
                "App::Property", "Apply LeadInOut to layers within an operation"
            ),
        )

        self.wire = None
        self.rapids = None

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    def setup(self, obj):
        op = PathDressup.baseOp(obj.Base)  # Dressup may be nested
        obj.Length = op.ToolController.Tool.Diameter * 0.75
        obj.LeadIn = True
        obj.LeadOut = True
        obj.KeepToolDown = False
        # obj.UseMachineCRC = False
        obj.StyleOn = "Arc"
        obj.StyleOff = "Arc"
        # obj.RadiusCenter = "Radius"
        obj.ExtendLeadIn = 0
        obj.ExtendLeadOut = 0
        obj.RapidPlunge = False
        obj.IncludeLayers = True

    def execute(self, obj):
        op = PathDressup.baseOp(obj.Base)  # Dressup may be nested
        if not op:
            return
        if not op.isDerivedFrom("Path::Feature"):
            return
        if not op.Path:
            return
        if obj.Length < 0:
            PathLog.error(
                translate("Path_DressupLeadInOut", "Length/Radius positive not Null")
                + "\n"
            )
            obj.Length = 0.1
        self.wire, self.rapids = PathGeom.wireForPath(obj.Base.Path)
        obj.Path = self.generateLeadInOutCurve(obj)

    def generateLeadInOutCurve(self, obj):
        op = PathDressup.baseOp(obj.Base)  # Dressup may be nested
        # global machine
        machine = PathMachineState.MachineState()

        # Marshall the arguments for the leadin generator
        leadinargs = {
            "segment": None,
            "leadIn": True
            "length": obj.Length,
            "style": obj.StyleOn,
            "extend": obj.ExtendLeadIn,
        }

        # Marshall the arguments for the leadout generator
        leadoutargs = {
            "segment": None,
            "leadIn": False
            "length": obj.Length,
            "style": obj.StyleOff,
            "extend": obj.ExtendLeadOut,
        }

        newpath = []

        # Iterate through all commands.  Find the first feed move following
        # one or more rapid moves. Generate a leadin. Add rapid moves to the
        # new start position. Insert the leadin.

        # Find the last feed move prior to a rapid move. Generate a leadout.
        # and insert it. Generate new rapids from the leadout position.

        for curCommand in op.Path.Commands:
            PathLog.debug(f"CurCMD: {curCommand}")

            # Don't worry about non-move commands, just add to output
            if curCommand.Name not in movecommands + CmdMoveRapid:
                newpath.append(curCommand)
                machine.addCommand(curCommand)
                continue

            if curCommand.Name in CmdMoveRapid:
                if newpath[-1].Name in movecommands:
                    # leadout needed
                    leadoutcommands = leadin_generator.generate(**leadoutargs)
                    for c in leadoutcommands:
                        newpath.append(c)
                        machine.addCommand(curCommand)

                    # Explicitly retract to safeheight
                    endpos = leadoutcommands[-1]
                    command = Path.Command(
                        "G0", {"X": endpos.x, "Y": endpos.y, "Z": curCommand.z}
                    )
                    newpath.append(command)
                    machine.addCommand(curCommand)
                else:
                    newpath.append(curCommand)
                    machine.addCommand(curCommand)

                continue

            if curCommand.Name in movecommands:

                PathLog.debug(f"last: {newpath[-1].Name}")
                last = newpath[-1]
                if last.Name in CmdMoveRapid:
                    if curCommand.z != last.z: # Old entry feed move
                        command = Path.Command(
                            "G0", {"X": curCommand.x, "Y": curCommand.y, "Z": curCommand.z}
                        )
                        if machine.addCommand(curCommand):
                            newpath.append(command)
                        continue

                    # leadin needed
                    lastpoint = machine.getPosition()
                    edge = PathGeom.edgeForCmd(curCommand, lastpoint)
                    leadinargs['segment'] = edge
                    leadincommands = leadin_generator.generate(**leadinargs)

                    # extract the new start point and rapid to safe height
                    # above
                    startpos = leadincommands[0]
                    command = Path.Command(
                        "G0", {"X": startpos.x, "Y": startpos.y, "Z": curCommand.z}
                    )
                    newpath.append(command)
                    machine.addCommand(command)

                    for c in leadincommands:
                        newpath.append(c)
                        machine.addCommand(c)

                    newpath.append(curCommand)
                    machine.addCommand(curCommand)

                else:
                    newpath.append(curCommand)
                    machine.addCommand(curCommand)

        PathLog.debug(len(newpath))
        return Path.Path(newpath)


class TaskDressupLeadInOut(SimpleEditPanel):
    _transaction_name = "Edit LeadInOut Dress-up"
    _ui_file = ":/panels/DressUpLeadInOutEdit.ui"

    def setupUi(self):
        self.connectWidget("LeadIn", self.form.chkLeadIn)
        self.connectWidget("LeadOut", self.form.chkLeadOut)
        self.connectWidget("Length", self.form.dsbLen)
        self.connectWidget("ExtendLeadIn", self.form.dsbExtendIn)
        self.connectWidget("ExtendLeadOut", self.form.dsbExtendOut)
        self.connectWidget("StyleOn", self.form.cboStyleIn)
        self.connectWidget("StyleOff", self.form.cboStyleOut)
        self.connectWidget("RadiusCenter", self.form.cboRadius)
        self.connectWidget("RapidPlunge", self.form.chkRapidPlunge)
        self.connectWidget("IncludeLayers", self.form.chkLayers)
        self.connectWidget("KeepToolDown", self.form.chkKeepToolDown)
        # self.connectWidget("UseMachineCRC", self.form.chkUseCRC)
        self.setFields()


class ViewProviderDressup:
    def __init__(self, vobj):
        self.obj = vobj.Object
        self.setEdit(vobj)

    def attach(self, vobj):
        self.obj = vobj.Object
        self.panel = None

    def claimChildren(self):
        if hasattr(self.obj.Base, "InList"):
            for i in self.obj.Base.InList:
                if hasattr(i, "Group"):
                    group = i.Group
                    for g in group:
                        if g.Name == self.obj.Base.Name:
                            group.remove(g)
                    i.Group = group
                    print(i.Group)
        return [self.obj.Base]

    def setEdit(self, vobj, mode=0):
        FreeCADGui.Control.closeDialog()
        panel = TaskDressupLeadInOut(vobj.Object, self)
        FreeCADGui.Control.showDialog(panel)
        return True

    def unsetEdit(self, vobj, mode=0):
        if self.panel:
            self.panel.abort()

    def onDelete(self, arg1=None, arg2=None):
        """this makes sure that the base operation is added back to the project and visible"""
        PathLog.debug("Deleting Dressup")
        if arg1.Object and arg1.Object.Base:
            FreeCADGui.ActiveDocument.getObject(arg1.Object.Base.Name).Visibility = True
            job = PathUtils.findParentJob(self.obj)
            if job:
                job.Proxy.addOperation(arg1.Object.Base, arg1.Object)
            arg1.Object.Base = None
        return True

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    def clearTaskPanel(self):
        self.panel = None


class CommandPathDressupLeadInOut:
    def GetResources(self):
        return {
            "Pixmap": "Path_Dressup",
            "MenuText": QT_TRANSLATE_NOOP("Path_DressupLeadInOut", "LeadInOut Dressup"),
            "ToolTip": QT_TRANSLATE_NOOP(
                "Path_DressupLeadInOut",
                "Creates a Cutter Radius Compensation G41/G42 Entry Dressup object from a selected path",
            ),
        }

    def IsActive(self):
        op = PathDressup.selection()
        if op:
            return not PathDressup.hasEntryMethod(op)
        return False

    def Activated(self):
        # check that the selection contains exactly what we want
        selection = FreeCADGui.Selection.getSelection()
        if len(selection) != 1:
            PathLog.error(
                translate("Path_DressupLeadInOut", "Please select one path object")
                + "\n"
            )
            return
        baseObject = selection[0]
        if not baseObject.isDerivedFrom("Path::Feature"):
            PathLog.error(
                translate("Path_DressupLeadInOut", "The selected object is not a path")
                + "\n"
            )
            return
        if baseObject.isDerivedFrom("Path::FeatureCompoundPython"):
            PathLog.error(
                translate("Path_DressupLeadInOut", "Please select a Profile object")
            )
            return

        # everything ok!
        FreeCAD.ActiveDocument.openTransaction("Create LeadInOut Dressup")
        FreeCADGui.addModule("PathScripts.PathDressupLeadInOut")
        FreeCADGui.addModule("PathScripts.PathUtils")
        FreeCADGui.doCommand(
            'obj = FreeCAD.ActiveDocument.addObject("Path::FeaturePython", "LeadInOutDressup")'
        )
        FreeCADGui.doCommand(
            "dbo = PathScripts.PathDressupLeadInOut.ObjectDressup(obj)"
        )
        FreeCADGui.doCommand("base = FreeCAD.ActiveDocument." + selection[0].Name)
        FreeCADGui.doCommand("job = PathScripts.PathUtils.findParentJob(base)")
        FreeCADGui.doCommand("obj.Base = base")
        FreeCADGui.doCommand("job.Proxy.addOperation(obj, base)")
        FreeCADGui.doCommand("dbo.setup(obj)")
        FreeCADGui.doCommand(
            "obj.ViewObject.Proxy = PathScripts.PathDressupLeadInOut.ViewProviderDressup(obj.ViewObject)"
        )
        FreeCADGui.doCommand(
            "Gui.ActiveDocument.getObject(base.Name).Visibility = False"
        )
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


if FreeCAD.GuiUp:
    # register the FreeCAD command
    FreeCADGui.addCommand("Path_DressupLeadInOut", CommandPathDressupLeadInOut())

PathLog.notice("Loading Path_DressupLeadInOut... done\n")
