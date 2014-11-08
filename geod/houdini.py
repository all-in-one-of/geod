import itertools
import os
import re

from geod.core import BaseDumper, BaseLoader

import hou


def save_obj(geo, fh):

    N_vattr = geo.findVertexAttrib('N')
    N_pattr = geo.findPointAttrib('N')

    uv_vattr = geo.findVertexAttrib('uv')
    uv_pattr = geo.findPointAttrib('uv')

    for point in geo.points():
        fh.write('v %f %f %f\n' % tuple(point.position()))

    N_count = 0
    uv_count = 0

    faces = []

    for prim in geo.prims():

        face_parts = []

        for vert in prim.vertices():
            
            if N_vattr:
                N = vert.floatListAttribValue(N_vattr)
            elif N_pattr:
                N = vert.point().floatListAttribValue(N_pattr)
            else:
                N = None

            if N:
                N_count += 1
                fh.write('vn %f %f %f\n' % tuple(N))

            if uv_vattr:
                uv = vert.floatListAttribValue(uv_vattr)
            elif uv_pattr:
                uv = vert.point().floatListAttribValue(uv_pattr)
            else:
                uv = None

            if uv:
                uv_count += 1
                fh.write('vt %f %f %f\n' % tuple(uv))

            face_parts.append('%d/%s/%s' % (
                vert.point().number() + 1,
                uv_count if uv else '',
                N_count if N else '',
            ))

        fh.write('f %s\n' % ' '.join(reversed(face_parts)))


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

                    world = node.worldTransform()
                    try:
                        p_transform = node.parent().worldTransform()
                    except AttributeError:
                        local = world
                    else:
                        local = world * p_transform.inverted()
                    
                    obj['transform'] = {
                        'world': world.asTuple(),
                        'local': local.asTuple(),
                        'transform_order': node.parm('xOrd').evalAsString(),
                        'rotation_order': node.parm('rOrd').evalAsString(),
                        'pivot': node.parmTuple('p').eval(),
                    }
                    
                    yield obj


    def dump_geo(self, obj):
        if obj.get('geometry'):
            node = hou.node('/obj/' + obj['path'])
            geo = node.displayNode().geometry()
            with open(self.abspath(obj['path'] + '.obj'), 'w') as fh:
                save_obj(geo, fh)


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

        node_path = node_path.replace(' ', '_')
        
        obj['_node_path'] = unique_node_name(node_path)
        obj['_node_name'] = os.path.basename(obj['_node_path'])
        obj['_node_dir'] = os.path.dirname(obj['_node_path'])

        loader = getattr(self, '_load_%s' % obj['type'], None)
        if not loader:
            raise ValueError('unknown object type %r' % obj['type'])
        loader(obj)

    def _restore_transform(self, node, obj):

        transform = obj.get('transform')
        if not transform:
            return

        try:
            parent = node.parent()
        except:
            parent = None

        if False and 'parent_inverse' in transform:
            
            p_inv = hou.Matrix4(transform['parent_inverse'])
            if parent:
                pre_trans = parent.createNode('null', node.name() + '_parent_inverse')
                node.setInput(0, pre_trans)
                pre_trans.setParmTransform(p_inv)

            basis = hou.Matrix4(transform['basis'])
            node.setParmTransform(basis)

        elif 'local' in transform:
            m = hou.Matrix4(transform['local'])
            node.setParmTransform(m)
            parm = node.parmTransform()
            pre = parm.inverted() * m
            node.setPreTransform(pre)

        elif 'world' in transform:
            m = hou.Matrix4(transform['world'])
            node.setWorldTransform(m)

        else:
            raise ValueError('no acceptable matrix in transform')

    def _load_geometry(self, obj):
        print '# HoudiniLoader._load_geometry()', obj['_node_path']
        node = hou.node(obj['_node_dir']).createNode('geo', obj['_node_name'])
        self._restore_transform(node, obj)
        geo_path = self.abspath(os.path.join(obj['path'], '..', obj['geometry']['path']))
        file_ = node.node('file1')
        file_.parm('file').set(geo_path)
        file_.setHardLocked(True)


    def _load_group(self, obj):
        print '# HoudiniLoader._load_group()   ', obj['_node_path']
        node = hou.node(obj['_node_dir']).createNode('subnet', obj['_node_name'])
        self._restore_transform(node, obj)

    def _load_instance(self, obj):
        print '# HoudiniLoader._load_instance()', obj['_node_path']
        node = hou.node(obj['_node_dir']).createNode('instance', obj['_node_name'])
        self._restore_transform(node, obj)
        instance_path = os.path.join('..', obj['instance']['name'])
        node.parm('instancepath').set(instance_path)


def main_dump():
    dumper = HoudiniDumper('/Users/mikeboers/Desktop/test.geod')
    dumper.dump()

def main_load():
    loader = HoudiniLoader('/Users/mikeboers/Desktop/test.geod')
    loader.load()
