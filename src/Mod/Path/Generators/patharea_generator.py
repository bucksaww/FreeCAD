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


from numpy import ceil, linspace
import Path
import PathScripts.PathLog as PathLog

__title__ = "PathArea Path Generator"
__author__ = "sliptonic (Brad Collette)"
__url__ = "http://www.freecadweb.org"
__doc__ = "Generates a clearing path for a single AreaClearing targetshape"
__contributors__ = "russ4262 (Russell Johnson)"


if True:
    PathLog.setLevel(PathLog.Level.DEBUG, PathLog.thisModule())
    PathLog.trackModule(PathLog.thisModule())
else:
    PathLog.setLevel(PathLog.Level.INFO, PathLog.thisModule())

areaDefault = {
    "Accuracy": 0.01,
    "Angle": 45.0,
    "AngleShift": 0.0,
    "CleanDistance": 0.0,
    "ClipFill": 0,
    "ClipperScale": 10000.0,
    "Coplanar": 0,
    "Deflection": 0.01,
    "EndType": 0,
    "Explode": False,
    "ExtraPass": 0,
    "Fill": 0,
    "FitArcs": True,
    "FromCenter": True,
    "JoinType": 0,
    "MaxArcPoints": 100,
    "MinArcPoints": 4,
    "MiterLimit": 2.0,
    "Offset": 0.0,
    "OpenMode": 0,
    "PocketExtraOffset": 0.0,
    "PocketMode": 1,
    "PocketStepover": 0.0,
    "Project": False,
    "Reorient": True,
    "RoundPrecision": 0.0,
    "SectionCount": -1,
    "SectionMode": 2,
    "SectionOffset": 0.0,
    "SectionTolerance": 1e-5,
    "Shift": 0.0,
    "Simplify": False,
    "Stepdown": 1.0,
    "Stepover": 0.0,
    "SubjectFill": 0,
    "Thicken": False,
    "Tolerance": 1e-07,
    "ToolRadius": 1.0,
    "Unit": 1.0
}


def generate(
    shape,
    reference_plane,
    heights = []
    tool_diameter,
    step_over,

    start_point=None,
    direction="CW",
    startAt="Inside",
):
    """generate(edge, hole_radius, inner_radius, step_over) ... generate helix commands.
    hole_radius, inner_radius: outer and inner radius of the hole
    step_over: step over radius value"""

    params = areaDefault


    startpoint = edge.Vertexes[0].Point
    endpoint = edge.Vertexes[1].Point

    PathLog.track(
        "(helix: <{}, {}>\n hole radius {}\n inner radius {}\n step over {}\n start point {}\n end point {}\n step_down {}\n safeheight {}\n tool diameter {}\n direction {}\n startat {})".format(
            startpoint.x,
            startpoint.y,
            hole_radius,
            inner_radius,
            step_over,
            startpoint.z,
            endpoint.z,
            step_down,
            safeheight,
            tool_diameter,
            direction,
            startAt,
        )
    )

    if hole_radius < 0.0:
        raise ValueError("hole_radius < 0")

    if inner_radius > 0 and hole_radius - inner_radius < tool_diameter:
        raise ValueError(
            "hole_radius - inner_radius = {0} is < tool diameter of {1}".format(
                hole_radius - inner_radius, tool_diameter
            )
        )

    if inner_radius == 0.0 and not hole_radius > tool_diameter:
        raise ValueError(
            "Cannot helix a hole of diameter {0} with a tool of diameter {1}".format(
                2 * hole_radius, tool_diameter
            )
        )

    elif startAt not in ["Inside", "Outside"]:
        raise ValueError("Invalid value for parameter 'startAt'")

    elif direction not in ["CW", "CCW"]:
        raise ValueError("Invalid value for parameter 'direction'")

    if inner_radius > 0:
        PathLog.debug("(annulus mode)\n")
        hole_radius = hole_radius - tool_diameter / 2
        inner_radius = inner_radius + tool_diameter / 2
        if abs((hole_radius - inner_radius) / step_over) < 1e-5:
            radii = [(hole_radius + inner_radius) / 2]
        else:
            nr = max(int(ceil((hole_radius - inner_radius) / step_over)), 2)
            radii = linspace(hole_radius, inner_radius, nr)

    elif hole_radius <= 2 * step_over:
        PathLog.debug("(single helix mode)\n")
        radii = [hole_radius - tool_diameter / 2]
        if radii[0] <= 0:
            raise ValueError(
                "Cannot helix a hole of diameter {0} with a tool of diameter {1}".format(
                    2 * hole_radius, tool_diameter
                )
            )
    else:
        PathLog.debug("(full hole mode)\n")
        hole_radius = hole_radius - tool_diameter / 2
        inner_radius = step_over / 2

        nr = max(1 + int(ceil((hole_radius - inner_radius) / step_over)), 2)
        radii = [r for r in linspace(hole_radius, inner_radius, nr) if r > 0]
        if not radii:
            raise ValueError(
                "Cannot helix a hole of diameter {0} with a tool of diameter {1}".format(
                    2 * hole_radius, tool_diameter
                )
            )
    nz = max(int(ceil((startpoint.z - endpoint.z) / step_down)), 2)
    zi = linspace(startpoint.z, endpoint.z, 2 * nz + 1)

    def helix_cut_r(r):
        commandlist = []
        arc_cmd = "G2" if direction == "CW" else "G3"
        commandlist.append(
            Path.Command("G0", {"X": startpoint.x + r, "Y": startpoint.y})
        )
        commandlist.append(Path.Command("G0", {"Z": safeheight}))
        commandlist.append(Path.Command("G1", {"Z": startpoint.z}))
        for i in range(1, nz + 1):
            commandlist.append(
                Path.Command(
                    arc_cmd,
                    {
                        "X": startpoint.x - r,
                        "Y": startpoint.y,
                        "Z": zi[2 * i - 1],
                        "I": -r,
                        "J": 0.0,
                    },
                )
            )
            commandlist.append(
                Path.Command(
                    arc_cmd,
                    {
                        "X": startpoint.x + r,
                        "Y": startpoint.y,
                        "Z": zi[2 * i],
                        "I": r,
                        "J": 0.0,
                    },
                )
            )
        commandlist.append(
            Path.Command(
                arc_cmd,
                {
                    "X": startpoint.x - r,
                    "Y": startpoint.y,
                    "Z": endpoint.z,
                    "I": -r,
                    "J": 0.0,
                },
            )
        )
        commandlist.append(
            Path.Command(
                arc_cmd,
                {
                    "X": startpoint.x + r,
                    "Y": startpoint.y,
                    "Z": endpoint.z,
                    "I": r,
                    "J": 0.0,
                },
            )
        )
        commandlist.append(Path.Command("G0", {"Z": safeheight}))
        return commandlist

    if startAt == "Inside":
        radii = radii[::-1]

    commands = []
    for r in radii:
        commands.extend(helix_cut_r(r))

    return commands
