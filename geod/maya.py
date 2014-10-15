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


class MayaLoader(BaseLoader):

    def load_object(self, obj):
        loader = getattr(self, '_load_%s' % obj['type'], None)
        if not loader:
            raise ValueError('unknown object type %r' % obj['type'])
        loader(obj)

    def _restore_transform(self, node, obj):
        transform = obj.get('transform')
        if not transform:
            return
        m = hou.Matrix4(transform['matrix'])
        try:
            m *= node.parent().worldTransform()
        except AttributeError:
            pass
        node.setWorldTransform(m)

    def _load_geometry(self, obj):
        print '# MayaLoader._load_geometry()', obj['path']

        if 'transform' in obj:
            self._load_group(obj)

        old_objs = set(mc.ls(assemblies=True))
        old_sets = set(mc.listSets(allSets=True))

        geo_path = self.abspath(os.path.join(obj['path'], '..', obj['geometry']['path']))
        # mo=0 signals to import into a single object.
        x = mc.file(geo_path, i=True, type="OBJ", options='mo=0')

        new_objs = list(set(mc.ls(assemblies=True)).difference(old_objs))

        # Lots of extra sets get created that we don't want.
        new_sets = list(set(mc.listSets(allSets=True)).difference(old_sets))
        mc.delete(new_sets)

        assert len(new_objs) == 1

        parent = obj.get('_parent')
        transform = obj.get('_transform') or parent['_transform']

        if parent:
            shape = mc.listRelatives(new_objs, fullPath=True, shapes=True)[0]
            new_shape = mc.parent(shape, transform, shape=True, relative=True)
            mc.rename(new_shape, obj['name'])
            mc.delete(new_objs)

    def _load_group(self, obj):
        print '# MayaLoader._load_group()', obj['path']
        parent = obj.get('_parent')
        transform = mc.createNode('transform', name=obj['name'], parent=parent['_transform'] if parent else None)
        mc.xform(transform, objectSpace=True, matrix=obj['transform']['matrix'])
        obj['_transform'] = transform

    def _load_instance(self, obj):
        print '# MayaLoader._load_instance()', obj['path']
        return

def main_dump():
    dumper = MayaDumper('/Users/mikeboers/Desktop/test.geod')
    dumper.dump()

def main_load():
    loader = MayaLoader('/Users/mikeboers/Desktop/test.geod')
    loader.load()
