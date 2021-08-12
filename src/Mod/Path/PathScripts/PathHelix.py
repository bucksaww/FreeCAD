# -*- coding: utf-8 -*-
# ***************************************************************************
# *   Copyright (c) 2016 Lorenz Hüdepohl <dev@stellardeath.org>             *
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

from Generators import helix_generator as generator
import FreeCAD
import Path
import PathMachineState
import PathRotation
import PathScripts.PathCircularHoleBase as PathCircularHoleBase
import PathScripts.PathLog as PathLog
import PathScripts.PathOp as PathOp
import PathFeedRate

from PySide import QtCore

__title__ = "Path Helix Drill Operation"
__author__ = "Lorenz Hüdepohl"
__url__ = "https://www.freecadweb.org"
__doc__ = "Class and implementation of Helix Drill operation"
__contributors__ = "russ4262 (Russell Johnson)"
__created__ = "2016"
__scriptVersion__ = "1b testing"
__lastModified__ = "2019-07-12 09:50 CST"


if True:
        PathLog.setLevel(PathLog.Level.DEBUG, PathLog.thisModule())
        PathLog.trackModule(PathLog.thisModule())
else:
        PathLog.setLevel(PathLog.Level.INFO, PathLog.thisModule())

def translate(context, text, disambig=None):
    return QtCore.QCoreApplication.translate(context, text, disambig)

class ObjectHelix(PathCircularHoleBase.ObjectOp):
    """Proxy class for Helix operations."""

    def circularHoleFeatures(self, obj):
        """circularHoleFeatures(obj) ... enable features supported by Helix."""
        return PathOp.FeatureSpots | PathOp.FeatureCoolant

    def initCircularHoleOperation(self, obj):
        """initCircularHoleOperation(obj) ... create helix specific properties."""
        obj.addProperty(
            "App::PropertyEnumeration",
            "Direction",
            "Helix Drill",
            translate(
                "PathHelix",
                "The direction of the circular cuts, ClockWise (CW), or CounterClockWise (CCW)",
            ),
        )
        obj.Direction = ["CW", "CCW"]

        obj.addProperty(
            "App::PropertyEnumeration",
            "StartSide",
            "Helix Drill",
            translate("PathHelix", "Start cutting from the inside or outside"),
        )
        obj.StartSide = ["Inside", "Outside"]

        obj.addProperty(
            "App::PropertyLength",
            "StepOver",
            "Helix Drill",
            translate(
                "PathHelix", "Radius increment (must be smaller than tool diameter)"
            ),
        )
        obj.addProperty(
            "App::PropertyLength",
            "StepDown",
            "Helix Drill",
            translate("PathHelix", "step down value"),
        )

        obj.addProperty(
            "App::PropertyLength",
            "StartRadius",
            "Helix Drill",
            translate("PathHelix", "Starting Radius"),
        )

    def opOnDocumentRestored(self, obj):
        if not hasattr(obj, "StartRadius"):
            obj.addProperty(
                "App::PropertyLength",
                "StartRadius",
                "Helix Drill",
                translate("PathHelix", "Starting Radius"),
            )

    def circularHoleExecute(self, obj):
        """circularHoleExecute(obj, holes) ... generate helix commands for each hole in holes"""
        PathLog.track()
        machine = PathMachineState.MachineState()

        self.commandlist.append(Path.Command("(helix cut operation)"))

        # rapid to clearance height
        command = Path.Command(
            "G0", {"Z": obj.ClearanceHeight.Value, "F": self.vertRapid}
        )
        machine.addCommand(command)
        self.commandlist.append(command)

        # Op can store both individual targets and target groups. Flatten the
        # list
        flatlist = []
        for target in obj.Group:
            target = getattr(target, "LinkedObject", target)
            flatlist.extend(getattr(target, "Group", [target]))

        # if any location sorting is needed, it should be done here
        # holes = PathUtils.sort_jobs(holes, ['x', 'y'])

        PathLog.track(flatlist)
        for target in flatlist:
            if not target.Active:
                continue
            (edge, diam) = target.Proxy.getShape(target)
            try:
                rotation, edge = PathRotation.setRotationForEdgeCA(
                    edge, aMin=0, aMax=90
                )
            except ValueError:
                FreeCAD.Console.PrintWarning(
                    "Target {} is not reachable with the current configuration\n".format(
                        target.Label
                    )
                )
                continue

            # Add offsets for start and endpoint
            startpoint = edge.Vertexes[0].Point

            # if rotation is needed, reposition safely
            if machine.A != rotation["A"] or machine.C != rotation["C"]:

                # Move to clearance height
                command = Path.Command(
                    "G0", {"Z": obj.ClearanceHeight.Value, "F": self.vertRapid}
                )
                self.commandlist.append(command)
                machine.addCommand(command)

                # Perform Rotation
                command = Path.Command(
                    "G0 A{} C{}".format(rotation["A"], rotation["C"])
                )
                self.commandlist.append(command)
                machine.addCommand(command)

            # Move to start point
            startpoint = edge.Vertexes[0].Point
            command = Path.Command(
                "G0 X{} Y{} Z{}".format(startpoint.x, startpoint.y, startpoint.z)
            )
            self.commandlist.append(command)
            machine.addCommand(command)

            # Perform helix move
            commands = generator.generate(
                edge=edge,
                hole_radius=diam / 2,
                step_down=obj.StepDown.Value,
                step_over=(float(obj.StepOver.Value) / 50.0) * self.radius,
                tool_diameter=obj.ToolController.Tool.Diameter.Value,
                safeheight=obj.SafeHeight.Value,
                inner_radius=obj.StartRadius.Value,
                direction=obj.Direction,
                startAt=obj.StartSide,
            )
            self.commandlist.extend(commands)
            for c in commands:
                machine.addCommand(c)

        PathFeedRate.setFeedRate(self.commandlist, obj.ToolController)

    def opSetDefaultValues(self, obj, job):
        obj.Direction = "CW"
        obj.StartSide = "Inside"
        obj.StepOver = 100


def SetupProperties():
    setup = []
    setup.append("Direction")
    setup.append("StartSide")
    setup.append("StepOver")
    setup.append("StartRadius")
    return setup


def Create(name, obj=None, parentJob=None):
    '''Create(name) ... Creates and returns a Helix operation.'''
    if obj is None:
        obj = FreeCAD.ActiveDocument.addObject("Path::FeaturePython", name)
    obj.Proxy = ObjectHelix(obj, name, parentJob)
    if obj.Proxy:
        obj.Proxy.findAllHoles(obj)
    return obj
