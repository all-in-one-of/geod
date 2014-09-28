import itertools
import os
import re

from geod.core import BaseDumper, BaseLoader

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
                if isinstance(node, hou.ObjNode) and type_ in ('subnet', 'geo', 'instance'):

                    obj = {
                        'generator': 'Houdini %s' % hou.applicationVersionString(),
                        'hou_node': node.path(),
                        'hou_type': '%s/%s' % (node.type().category().name().lower(), node.type().name()),
                        'name': node.name(),
                        'path': os.path.relpath(node.path(), '/obj'),
                    }
                    if type_ == 'geo':
                        obj['geometry_file'] = obj['path'] + '.obj'
                    if type_ == 'instance':
                        instance = node.parm('instancepath').evalAsString()
                        instance = os.path.abspath(os.path.join(node.path(), instance))
                        instance = os.path.relpath(instance, os.path.dirname(node.path()))
                        obj['instance_name'] = instance

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

    def dump_geo(self, obj):
        if obj.get('geometry_file'):
            node = hou.node('/obj/' + obj['path'])
            geo = node.displayNode().geometry()
            geo.saveToFile(self.abspath(obj['geometry_file']))


def unique_node_name(base):
    node = hou.node(base)
    if not node:
        return base
    for i in itertools.count(1):
        path = '%s_%d' % (base, i)
        node = hou.node(path)
        if not node:
            return path


class HoudiniLoader(BaseLoader):

    def load_object(self, obj):

        parent = obj['_parent']
        if parent:
            node_path = os.path.join(parent['_node_path'], obj['name'])
        else:
            node_path = '/obj/' + obj['path']

        node_path = unique_node_name(node_path)
        node_dir = os.path.dirname(node_path)
        obj['_node_path'] = node_path

        if 'geometry_file' in obj:
            self._load_geometry(obj)
        else:
            self._load_subnet(obj)

    def _load_geometry(self, obj):
        print '# HoudiniLoader._load_geometry()', obj['_node_path']

    def _load_subnet(self, obj):
        print '# HoudiniLoader._load_subnet()', obj['_node_path']


def main_dump():
    dumper = HoudiniDumper('/Users/mikeboers/Desktop/test.geod')
    dumper.dump()

def main_load():
    loader = HoudiniLoader('/Users/mikeboers/Desktop/test.geod')
    loader.load()
