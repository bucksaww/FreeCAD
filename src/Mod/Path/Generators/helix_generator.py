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

__title__ = "Helix Path Generator"
__author__ = "sliptonic (Brad Collette)"
__url__ = "http://www.freecadweb.org"
__doc__ = "Generates the helix for a single spot targetshape"
__contributors__ = "russ4262 (Russell Johnson), Lorenz Hüdepohl"


if True:
    PathLog.setLevel(PathLog.Level.DEBUG, PathLog.thisModule())
    PathLog.trackModule(PathLog.thisModule())
else:
    PathLog.setLevel(PathLog.Level.INFO, PathLog.thisModule())


def generate(
    edge,
    hole_radius,
    step_down,
    step_over,
    tool_diameter,
    safeheight,
    inner_radius=0.0,
    direction="CW",
    startAt="Inside",
):
    """generate(edge, hole_radius, inner_radius, step_over) ... generate helix commands.
    hole_radius, inner_radius: outer and inner radius of the hole
    step_over: step over radius value"""

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
