import maya.cmds as mc

from ..scene import Scene
from .object import MayaObject as Object


def dump():
    scene = Scene('/Users/mikeboers/Desktop/test.geod', object_class=Object)

    selection = mc.ls(selection=True, long=True) or []
    transforms = mc.listRelatives(selection, allDescendents=True, fullPath=True, type='transform') or []
    transforms.extend(x for x in selection if mc.nodeType(x) == 'transform')

    for transform in transforms:
        scene.add_object(Object(transform))
    scene.finalize_graph()
    scene.dump()


def load():    
    scene = Scene('/Users/mikeboers/Desktop/test.geod', object_class=Object)
    scene.load()
