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
                        'houdini': {
                            'path': node.path(),
                            'context': node.type().category().name().lower(),
                            'type': node.type().name(),
                        },
                        'name': node.name(),
                        'path': os.path.relpath(node.path(), '/obj'),
                        'type': {'subnet': 'group', 'geo': 'geometry'}.get(type_, type_),
                    }

                    if type_ == 'geo':
                        obj['geometry'] = {
                            'path': obj['name'] + '.obj',
                        }

                    if type_ == 'instance':
                        instance = node.parm('instancepath').evalAsString()
                        instance = os.path.abspath(os.path.join(node.path(), instance))
                        instance = os.path.relpath(instance, os.path.dirname(node.path()))
                        obj['instance'] = {
                            'name': instance,
                        }

                    transform = node.worldTransform()
                    try:
                        p_transform = node.parent().worldTransform()
                    except AttributeError:
                        pass
                    else:
                        transform *= p_transform.inverted()
                    
                    obj['transform'] = {
                        'matrix': transform.asTuple(),
                        'transform_order': node.parm('xOrd').evalAsString(),
                        'rotation_order': node.parm('rOrd').evalAsString(),
                        'pivot': node.parmTuple('p').eval(),
                    }
                    
                    yield obj

    def dump_geo(self, obj):
        if obj.get('geometry'):
            node = hou.node('/obj/' + obj['path'])
            geo = node.displayNode().geometry()
            geo.saveToFile(self.abspath(obj['path'] + '.obj'))


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

        obj['_node_path'] = unique_node_name(node_path)
        obj['_node_name'] = os.path.basename(obj['_node_path'])
        obj['_node_dir'] = os.path.dirname(obj['_node_path'])

        loader = getattr(self, '_load_%s' % obj['type'], None)
        if not loader:
            raise ValueError('unknown object type %r' % obj['type'])
        loader(obj)

    def _restore_transform(self, node, transform):
        m = hou.Matrix4(transform['matrix'])
        try:
            m *= node.parent().worldTransform()
        except AttributeError:
            pass
        node.setWorldTransform(m)

    def _load_geometry(self, obj):
        print '# HoudiniLoader._load_geometry()', obj['_node_path']
        node = hou.node(obj['_node_dir']).createNode('geo', obj['_node_name'])
        self._restore_transform(node, obj['transform'])
        geo_path = self.abspath(os.path.join(obj['path'], '..', obj['geometry']['path']))
        node.node('file1').parm('file').set(geo_path)

    def _load_group(self, obj):
        print '# HoudiniLoader._load_group()', obj['_node_path']
        node = hou.node(obj['_node_dir']).createNode('subnet', obj['_node_name'])
        self._restore_transform(node, obj['transform'])

    def _load_instance(self, obj):
        print '# HoudiniLoader._load_instance()', obj['_node_path']
        node = hou.node(obj['_node_dir']).createNode('instance', obj['_node_name'])
        self._restore_transform(node, obj['transform'])
        instance_path = os.path.join('..', obj['instance']['name'])
        node.parm('instancepath').set(instance_path)


def main_dump():
    dumper = HoudiniDumper('/Users/mikeboers/Desktop/test.geod')
    dumper.dump()

def main_load():
    loader = HoudiniLoader('/Users/mikeboers/Desktop/test.geod')
    loader.load()
