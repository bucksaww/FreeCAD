from FreeCAD import Vector
import Part
import Path
import PathScripts.PathGeom as PathGeom
import PathScripts.PathLog as PathLog
import math

if True:
    PathLog.setLevel(PathLog.Level.DEBUG, PathLog.thisModule())
    PathLog.trackModule(PathLog.thisModule())
else:
    PathLog.setLevel(PathLog.Level.INFO, PathLog.thisModule())


def generate(
    segment,
    leadIn=True,
    direction="CCW",
    arcRadius=10,
    style="Arc",
    extendLength=10,
):

    """
    Generates a LeadInOut Path.
    segment is the edge representing the geometry to lead in to
    leadinout determines whether we generate a leadin or leadout
    direction indicates travel. This implies which side of the segment is safe to enter from
    arcRadius is the radius of an 'Arc' style leadin.
    style indicates the type of leadin; Arc, Perpendicular, or Tangent
    extendLength is the length of a straight segment added.

    extendLength and arcRadius can be used together in Arc style leadin.

    """
    PathLog.debug(
        f"LeadIn: {leadIn}, arcRadius: {arcRadius} style: {style} extendLength: {extendLength}"
    )

    if PathLog.debug:
        Part.show(segment)

    if not leadIn:
        # Reverse the segment.  A leadout is just a leadin from the other end.
        # We'll also reverse the wire at the end before generating the Path
        # Commands
        segment = PathGeom.flipEdge(segment)

    segStart = segment.firstVertex().Point
    PathLog.debug(f"segstart: {segStart}")
    segEnd = segment.lastVertex().Point
    PathLog.debug(segEnd)

    dir1 = segment.tangentAt(segment.FirstParameter) * -1
    perp = dir1.cross(Vector(0, 0, 1))

    el = (
        extendLength
        if direction == "CW" and style == "Perpendicular"
        else -extendLength
    )

    if style == "Perpendicular":
        startPoint = Vector(perp.multiply(el)) + segStart

        PathLog.debug(f"Perpendicular: Make line from {startPoint} to {segStart}")
        line = Part.makeLine(startPoint, segStart)
        resultwire = Part.Wire([line])

    elif style == "Tangent":
        startPoint = Vector(dir1.multiply(el)) + segStart

        PathLog.debug(f"Tangent: Make line from {startPoint} to {segStart}")
        line = Part.makeLine(startPoint, segStart)
        resultwire = Part.Wire([line])

    else:  # style == "Arc"
        rad = arcRadius if direction == "CCW" else -arcRadius
        arcCenter = Vector(perp.multiply(rad)) + segStart

        # Calculate the in and out angle to generate a 90 arc
        a1 = math.degrees(PathGeom.getAngle(dir1))
        PathLog.debug(f"a1: {a1}")
        if direction == "CCW":
            a2 = (a1 + 90) % 360
            PathLog.debug(f"a2: {a2}")
            inangle = a1
            outangle = a2
        else:
            a2 = (a1 - 90) % 360
            PathLog.debug(f"a2: {a2}")
            inangle = a2
            outangle = a1

        newArc = Part.makeCircle(
            math.fabs(arcRadius), arcCenter, Vector(0, 0, 1), inangle, outangle
        )
        PathLog.debug(
            f"Arc: center: {arcCenter} inangle: {inangle} outangle: {outangle}"
        )

        if PathGeom.pointsCoincide(newArc.firstVertex().Point, segStart):
            newArc = PathGeom.flipEdge(newArc)

        edges = [newArc]
        if extendLength > 0:  # Add the straight extension segment
            dir1 = newArc.tangentAt(newArc.FirstParameter)
            segStart = newArc.firstVertex().Point
            startPoint = Vector(dir1.multiply(el)) + segStart
            edges.append(Part.makeLine(startPoint, segStart))

        resultwire = Part.Wire(edges)

    # make sure the wire is oriented correctly
    if leadIn and PathGeom.pointsCoincide(resultwire.Vertexes[0].Point, segStart):
        resultwire = PathGeom.flipWire(resultwire)

    elif not leadIn and not PathGeom.pointsCoincide(
        resultwire.Vertexes[0].Point, segStart
    ):
        resultwire = PathGeom.flipWire(resultwire)

    if PathLog.debug:
        Part.show(resultwire)

    # Generate the Path Commands
    commands = []
    if leadIn:
        # We'll explicitly  add a feed move to the start position.
        firstpos = resultwire.Vertexes[0].Point
        command = Path.Command(
            "G1", {"X": firstpos.x, "Y": firstpos.y, "Z": firstpos.z}
        )
        commands.append(command)

    for e in resultwire.Edges:
        commands.extend(PathGeom.cmdsForEdge(e))

    PathLog.debug(commands)

    return commands
