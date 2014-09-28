from __future__ import absolute_import

import itertools
import os
import re

import mayatools.context

from geod.core import BaseDumper, BaseLoader

import maya.cmds as mc


class MayaDumper(BaseDumper):

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

    def iter_objects(self):

        selection = mc.ls(selection=True, long=True) or []
        transforms = mc.listRelatives(selection, allDescendents=True, fullPath=True, type='transform') or []
        transforms.extend(x for x in selection if mc.nodeType(x) == 'transform')

        for t in sorted(set(transforms)):

            has_children = bool(mc.listRelatives([t], type='transform'))

            shapes = mc.listRelatives([t], fullPath=True, shapes=True)
            shape = shapes[0] if shapes else None
            if len(shapes) > 1:
                print 'WARNING: more than one shape for', t

            obj = self._obj_base(t)

            if shape and has_children:
                # We need to split this one up!

                self._obj_transform(obj)
                yield obj

                obj = self._obj_base(shape)
                obj['maya']['transform'] = t
                self._obj_geometry(obj)
                yield obj

            elif shape:
                self._obj_transform(obj)
                self._obj_geometry(obj)
                obj['maya']['mesh'] = shape
                yield obj

            else:
                # Not quite sure how we would get here...
                yield obj


    def dump_geo(self, obj):

        if not obj.get('geometry'):
            return

        transform = obj['maya']['transform']
        shape = obj['maya']['mesh']

        # We need to do the export in world space. Unfortunately, Maya won't
        # just do that for us.
        xform = mc.xform(transform, q=True, worldSpace=True, matrix=True)
        mc.xform(transform, worldSpace=True, matrix=[
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1,
        ])
        try:
            with mayatools.context.selection([shape], replace=True):
                mc.file(self.abspath(obj['path'] + '.obj'),
                    force=True,
                    exportSelected=True,
                    type="OBJexport",
                    options='materials=0',
                )
        finally:
            mc.xform(transform, worldSpace=True, matrix=xform)




def main_dump():
    dumper = MayaDumper('/Users/mikeboers/Desktop/test.geod')
    dumper.dump()

def main_load():
    loader = MayaLoader('/Users/mikeboers/Desktop/test.geod')
    loader.load()
