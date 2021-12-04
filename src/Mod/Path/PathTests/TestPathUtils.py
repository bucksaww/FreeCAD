# -*- coding: utf-8 -*-
# ***************************************************************************
# *   Copyright (c) 2017 sliptonic <shopinthewoods@gmail.com>               *
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

import FreeCAD
import PathScripts.PathUtils as PathUtils

from PathTests.PathTestUtils import PathTestBase


class TestPathUtils(PathTestBase):
    def setUp(self):
        self.doc = FreeCAD.newDocument("TestPathUtils")

    def tearDown(self):
        FreeCAD.closeDocument("TestPathUtils")

    def test00(self):
        """test sort_jobs"""

        args = {"locations": [], "keys": ["x", "y"], "attractors": None}

        # test that empty list returns empty
        result = PathUtils.sort_jobs(**args)
        self.assertTrue(result == [])

        # test basic sorting
        args["locations"].append({"x": 1, "y": 1, "r": 2})
        args["locations"].append({"x": 3, "y": 1, "r": 2})
        args["locations"].append({"x": 2, "y": 1, "r": 2})
        result = PathUtils.sort_jobs(**args)
        self.assertTrue(result[0]["x"] == 1)
        self.assertTrue(result[1]["x"] == 2)
        self.assertTrue(result[2]["x"] == 3)
