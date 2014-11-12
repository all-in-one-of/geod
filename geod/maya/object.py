import itertools
import re

import maya.cmds as mc

import mayatools.context

from ..object import BaseObject


class MayaObject(BaseObject):
    
    @classmethod
    def from_meta(cls, meta, parent):
        # Need to do the ls to get the long name, since createNode only gives
        # us the short one.
        name = re.sub(r'[^\w/]+', '_', meta['name']).strip('_')
        mc.createNode('transform', name=name, parent=parent.transform if parent else None)
        selection = mc.ls(selection=True, long=True)
        assert len(selection) == 1
        return cls(selection[0])

    def __init__(self, transform):
        super(MayaObject, self).__init__(re.split(r'[:|]', transform)[-1])
        self.transform = transform
        shapes = mc.listRelatives([self.transform], fullPath=True, shapes=True) or []
        self.shape = shapes[0] if shapes else None
        if len(shapes) > 1:
            print 'WARNING: more than one shape for', transform
            for s in shapes:
                print '\t' + s

    @property
    def guid(self):
        return self.transform

    def _iter_child_args(self):
        transforms = mc.listRelatives([self.transform], fullPath=True, type='transform') or []
        for transform in transforms:
            yield (transform, )

    def get_basic_meta(self):
        meta = super(MayaObject, self).get_basic_meta()
        meta.update({
            'application': mc.about(product=True),
            'maya': {
                'transform': self.transform
            },
        })
        return meta

    def get_transforms(self):
        return {
            'local': mc.xform(self.transform, q=True, objectSpace=True, matrix=True),
            'world': mc.xform(self.transform, q=True, objectSpace=False, matrix=True),
        }

    def set_transforms(self, transforms):
        if 'local' in transforms:
            mc.xform(self.transform, objectSpace=True, matrix=transforms['local'])
        elif 'world' in transforms:
            mc.xform(self.transform, objectSpace=False, matrix=transforms['world'])
        else:
            raise ValueError('no acceptable matrix in transforms')

    def export_geo(self, path):

        if not self.shape:
            return

        path = path + '.obj'

        # We need to do the export in world space. Unfortunately, Maya won't
        # just do that for us.
        xform = mc.xform(self.transform, q=True, worldSpace=True, matrix=True)
        mc.xform(self.transform, worldSpace=True, matrix=[
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1,
        ])
        try:
            with mayatools.context.selection([self.shape], replace=True):
                mc.file(path,
                    force=True,
                    exportSelected=True,
                    type="OBJexport",
                    options='materials=0',
                )
        finally:
            mc.xform(self.transform, worldSpace=True, matrix=xform)

        return {'path': path}

    def import_geo(self, spec):

        old_objs = set(mc.ls(assemblies=True))
        old_sets = set(mc.listSets(allSets=True))

        # mo=0 signals to import into a single object.
        x = mc.file(spec['path'], i=True, type="OBJ", options='mo=0')

        new_objs = list(set(mc.ls(assemblies=True)).difference(old_objs))

        # Lots of extra sets get created that we don't want.
        new_sets = list(set(mc.listSets(allSets=True)).difference(old_sets))
        mc.delete(new_sets)

        if not new_objs:
            print 'No geometry in', spec['path']
            return
        assert len(new_objs) == 1

        shape = mc.listRelatives(new_objs, fullPath=True, shapes=True)[0]
        shape = mc.parent(shape, self.transform, shape=True, relative=True)
        self.shape = mc.rename(self.shape, self.name + 'Shape')
        mc.delete(new_objs)


