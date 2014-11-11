from __future__ import absolute_import, print_function

import itertools
import os
import re

from geod.core import BaseDumper, BaseLoader

import bpy


class BlenderDumper(BaseDumper):

    def _obj_base(self, node):
        return {
            'generator': {
                'application': 'Blender ' + bpy.app.version_string,
                'module': __name__,
            },
            'name': node.name,
            'path': self._node_path(node),
            'type': 'group',
        }

    def _obj_transform(self, obj):
        node = bpy.data.objects[obj['name']]
        obj.update({
            'transform': {
                # Blender is column oriented, and everything else is not.
                'basis': list(itertools.chain(*node.matrix_basis.transposed())),
                'parent_inverse': list(itertools.chain(*node.matrix_parent_inverse.transposed())),
                'local': list(itertools.chain(*node.matrix_local.transposed())),
                'world': list(itertools.chain(*node.matrix_world.transposed())),
            }
        })

    def _obj_geometry(self, obj):
        obj.update({
            'type': 'geometry',
            'geometry': {
                'path': obj['name'] + '.obj',
            },
        })

    def _walk_objects(self, objs):
        # For some reason that I can't explain, it actually makes a difference
        # if we do children or parents first. If we do parents first, then the
        # world matrices of the children get horribly distorted.
        for obj in objs:
            for x in self._walk_objects(obj.children):
                yield x
            yield obj

    def _node_path(self, node):
        parts = []
        while node:
            parts.append(node.name)
            node = node.parent
        return '/' + '/'.join(reversed(parts))

    def iter_objects(self):

        for node in self._walk_objects(bpy.context.selected_objects):

            if node.data and node.type != "MESH":
                continue

            obj = self._obj_base(node)

            if node.data and node.children:
                # We need to split this one up!

                self._obj_transform(obj)
                yield obj

                obj = self._obj_base(node)
                obj['path'] = obj['path'] + '/' + obj['name']
                self._obj_geometry(obj)
                yield obj

            elif node.data:
                self._obj_transform(obj)
                self._obj_geometry(obj)
                yield obj

            else:
                
                self._obj_transform(obj)
                yield obj

    def dump_geo(self, obj):

        if not obj.get('geometry'):
            return

        node = bpy.data.objects[obj['name']]

        selected = bpy.context.selected_objects
        for x in selected:
            x.select = False

        mesh = bpy.data.meshes.new('geod_export')
        copy = bpy.data.objects.new('geod_export', mesh)
        copy.data = node.data
        bpy.context.scene.objects.link(copy)
        copy.select = True

        print('>>>', node.name)

        try:
            bpy.ops.export_scene.obj(
                filepath=self.abspath(obj['path'] + '.obj'),
                use_selection=True,
                use_materials=False,
                use_triangles=False,
                use_normals=True,
                use_uvs=True,
                axis_forward='Y',
                axis_up='Z',
            )
        finally:
            print('<<<', node.name)

            bpy.ops.object.delete()
            bpy.data.meshes.remove(mesh)

            for x in selected:
                x.select = True


def main_dump():
    dumper = BlenderDumper('/Users/mikeboers/Desktop/test.geod')
    dumper.dump()

