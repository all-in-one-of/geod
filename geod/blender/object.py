from __future__ import print_function

import itertools
import re

import bpy

from ..object import BaseObject


class BlenderObject(BaseObject):
    
    @classmethod
    def from_meta(cls, meta, parent):
        # Need to do the ls to get the long name, since createNode only gives
        # us the short one.
        mc.createNode('transform', name=meta['name'], parent=parent.transform if parent else None)
        transform = mc.ls(selection=True, long=True)[0]
        return cls(transform)

    def __init__(self, node):
        super(BlenderObject, self).__init__(node.name)
        self.node = node

    @property
    def guid(self):
        parts = []
        node = self.node
        while node:
            parts.append(node.name)
            node = node.parent
        return '/' + '/'.join(reversed(parts))

    def _iter_child_args(self):
        for child in self.node.children:
            yield (child, )

    def get_basic_meta(self):
        meta = super(BlenderObject, self).get_basic_meta()
        meta.update({
            'application': 'Blender ' + bpy.app.version_string,
            'blender': {
                'type': self.node.type
            },
        })
        return meta

    def get_transforms(self):
        return {
            # 'basis': list(itertools.chain(*self.node.matrix_basis.transposed())),
            # 'parent_inverse': list(itertools.chain(*self.node.matrix_parent_inverse.transposed())),
            'local': list(itertools.chain(*self.node.matrix_local.transposed())),
            'world': list(itertools.chain(*self.node.matrix_world.transposed())),
        }

    def set_transforms(self, transforms):
        raise NotImplementedError()

    def export_geo(self, path):

        if not self.node.data or self.node.type != "MESH":
            return

        selected = bpy.context.selected_objects
        for x in selected:
            x.select = False

        mesh = bpy.data.meshes.new('geod_export')
        copy = bpy.data.objects.new('geod_export', mesh)
        copy.data = self.node.data
        bpy.context.scene.objects.link(copy)
        copy.select = True

        print('>>>', self.node.name)

        try:
            bpy.ops.export_scene.obj(
                filepath=path + '.obj',
                use_selection=True,
                use_materials=False,
                use_triangles=False,
                use_normals=True,
                use_uvs=True,
                axis_forward='Y',
                axis_up='Z',
            )
        finally:
            print('<<<', self.node.name)

            bpy.ops.object.delete()
            bpy.data.meshes.remove(mesh)

            for x in selected:
                x.select = True

        return {'path': path + '.obj'}


    def import_geo(self, spec):
        raise NotImplementedError()

