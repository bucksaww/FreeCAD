# -*- coding: utf-8 -*-
# ***************************************************************************
# *   Copyright (c) 2021 sliptonic <shopinthewoods@gmail.com>               *
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

import Path
import FreeCAD
import Generators.leadin_generator as leadin_generator
import Generators.leadout_generator as leadout_generator
import PathScripts.PathLog as PathLog
import PathTests.PathTestUtils as PathTestUtils
import Part

PathLog.setLevel(PathLog.Level.INFO, PathLog.thisModule())
PathLog.trackModule(PathLog.thisModule())


class TestPathLeadInGenerator(PathTestUtils.PathTestBase):
    def test00(self):
        """Test LeadIn Generator Return"""
        v1 = FreeCAD.Vector(0, 0, 10)
        v2 = FreeCAD.Vector(0, 0, 0)

        e = Part.makeLine(v1, v2)
        leadinargs = {
            "segment": e,
            "Length": 10,
            "Style": "Arc",
            "KeepToolDown": False,
            "RadiusCenter": "Radius",
            "Extend": 0,
        }


        result = leadin_generator.generate(**leadinargs)
        print(result)


    def test10(self):
        """Test leadout generator Return"""
        v1 = FreeCAD.Vector(0, 0, 10)
        v2 = FreeCAD.Vector(0, 0, 0)
        e = Part.makeLine(v1, v2)

        leadoutargs = {
            "segment": e,
            "Length": 10,
            "Style": "Arc",
            "KeepToolDown": False,
            "RadiusCenter": "Radius",
            "Extend": 0,
        }

        result = leadout_generator.generate(**leadoutargs)
        print(result)
