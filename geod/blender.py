from __future__ import absolute_import, print_function

import itertools
import os
import re

from geod.core import BaseDumper, BaseLoader

import bpy


class BlenderDumper(BaseDumper):

    def _obj_base(self, path):
        return {
            'generator': mc.about(product=True),
            'maya': {mc.nodeType(path): path},
            'name': re.split(r'[:|]', path)[-1],
            'path': re.sub(r'[:|]', '/', path),
            'type': 'group',
        }

    def _obj_transform(self, obj):
        obj.update({
            'transform': {
                'matrix': mc.xform(obj['maya']['transform'], q=True, objectSpace=True, matrix=True),
            }
        })

    def _obj_geometry(self, obj):
        obj.update({
            'type': 'geometry',
            'geometry': {
                'path': obj['name'] + '.obj',
            }
        })

    def _walk_objects(self, objs):
        for obj in objs:
            yield obj
            for x in self._walk_objects(obj.children):
                yield x

    def _node_path(self, node):
        parts = []
        while node:
            parts.append(node.name)
            node = node.parent
        return '/' + '/'.join(reversed(parts))

    def iter_objects(self):

        for node in self._walk_objects(bpy.context.selected_objects):

            yield {
                'generator': 'Blender ' + bpy.app.version_string,
                'name': node.name,
                'path': self._node_path(node),
                'type': 'group',
                'transform': {
                    'matrix': list(itertools.chain(*node.matrix_local.transposed())),
                }
            }

            if node.data:
                yield {
                    'generator': 'Blender ' + bpy.app.version_string,
                    'name': node.name,
                    'path': self._node_path(node) + '/' + node.name,
                    'type': 'geometry',
                    'geometry': {
                        'path': node.name + '.obj',
                    },
                }

    def dump_geo(self, obj):

        if not obj.get('geometry'):
            return

        node = bpy.data.objects[obj['name']]

        transform = node.matrix_world.copy()
        node.matrix_world = [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]

        selected = bpy.context.selected_objects
        for x in selected:
            x.select = False
        try:
            node.select = True
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
            node.matrix_world = transform
            node.select = False
            for x in selected:
                x.select = True


def main_dump():
    dumper = BlenderDumper('/Users/mikeboers/Desktop/test.geod')
    dumper.dump()

