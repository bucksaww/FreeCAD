from Shapes import TargetShape
import FreeCADGui


class TargetWatch(object):
    list = []

    def addSelection(self, docname, featurename, SubName, clickvector):
        obj = FreeCADGui.getDocument(docname).getObject(featurename).Object
        if hasattr(obj, "Proxy") and isinstance(obj.Proxy, TargetShape.TargetShape):
            if not obj.Visibility and obj not in self.list:
                self.list.append(obj)
            obj.Visibility = True

    def removeSelection(self, docname, featurename, SubName):
        obj = FreeCADGui.getDocument(docname).getObject(featurename).Object
        if hasattr(obj, "Proxy") and isinstance(obj.Proxy, TargetShape.TargetShape):
            if obj in self.list:
                self.list.remove(obj)
            obj.Visibility = False

    def clearSelection(self, changes):
        for i in self.list:
            i.Visibility = False
        self.list.clear()
