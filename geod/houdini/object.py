import hou

from ..object import BaseObject
from .obj import dump as dump_obj


class HoudiniObject(BaseObject):
    
    def __init__(self, node):
        super(HoudiniObject, self).__init__(node.name())
        self.node = node

    @property
    def guid(self):
        return self.node.path()

    def _iter_child_args(self):
        if isinstance(self.node, hou.ObjNode) and self.node.type().name() == 'subnet':
            for node in self.node.children():
                yield (node, )

    def get_basic_meta(self):
        meta = super(HoudiniObject, self).get_basic_meta()

        type_name = self.node.type().name()
        meta.update({
            'application': 'Houdini %s' % hou.applicationVersionString(),
            'houdini': {
                'path': self.node.path(),
                'context': self.node.type().category().name().lower(),
                'type': type_name,
            },
        })

        if type_name == 'instance':
            instance = node.parm('instancepath').evalAsString()
            instance = os.path.abspath(os.path.join(node.path(), instance))
            instance = os.path.relpath(instance, os.path.dirname(node.path()))
            meta['instance'] = instance

        elif type_name not in ('geo', 'subnet'):
            raise ValueError('cannot export %r' % type_name)

        return meta

    def get_transforms(self):

        # We need to manually calculate a local transform, because there is
        # the whole {pre,parm}Transform thing going on in Houdini.

        world = self.node.worldTransform()
        try:
            p_transform = self.node.parent().worldTransform()
        except AttributeError:
            local = world
        else:
            local = world * p_transform.inverted()
        
        return {
            'world': world.asTuple(),
            'local': local.asTuple(),
        }

    def export_geo(self, path):
        if self.node.type().name() == 'geo':
            geo = self.node.displayNode().geometry()
            path = path + '.obj'
            with open(path, 'w') as fh:
                dump_obj(geo, fh)
            return {'path': path}

