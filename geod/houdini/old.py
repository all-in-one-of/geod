import itertools
import os
import re

import hou


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


