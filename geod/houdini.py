import os

from geod.core import BaseDumper

import hou


class HoudiniDumper(BaseDumper):

    def _walk_node(self, node):
        yield node
        if isinstance(node, hou.ObjNode) and node.type().name() == 'subnet':
            for child in node.children():
                for x in self._walk_node(child):
                    yield x

    def iter_objects(self):
        roots = hou.selectedNodes()
        for root in roots:
            for node in self._walk_node(root):
                type_ = node.type().name()
                if isinstance(node, hou.ObjNode) and type_ in ('subnet', 'geo'):

                    obj = {
                        'generator': 'Houdini %s' % hou.applicationVersionString(),
                        'name': os.path.relpath(node.path(), '/obj'),
                    }
                    if type_ == 'geo':
                        obj['geometry_file'] = obj['name'] + '.obj'

                    transform = node.worldTransform()
                    try:
                        p_transform = node.parent().worldTransform()
                    except AttributeError:
                        pass
                    else:
                        transform *= p_transform.inverted()
                    obj['transform'] = transform.asTuple()
                    
                    obj['transform_order'] = node.parm('xOrd').evalAsString()
                    obj['transform_rotation_order'] = node.parm('rOrd').evalAsString()
                    obj['transform_pivot'] = node.parmTuple('p').eval()
                    
                    yield obj

    def dump_geo(self, name, geometry_file=None, **kw):
        if geometry_file:
            node = hou.node(name)
            geo = node.displayNode().geometry()
            geo.saveToFile(self.abspath(geometry_file))


def main_dump():

    dumper = HoudiniDumper('/Users/mikeboers/Desktop/test.geod')
    dumper.dump()
