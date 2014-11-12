import maya.cmds as mc

from ..scene import Scene
from .object import MayaObject as Object


def dump():

    path = mc.fileDialog2(dialogStyle=1, fileMode=2)
    path = path and path[0]
    if not path:
        return

    mc.progressWindow(
        title='Geo.D Export',
        status='Initializing...',
        progress=0,
        isInterruptable=True,
    )

    scene = Scene(path, object_class=Object)

    selection = mc.ls(selection=True, long=True) or []
    transforms = mc.listRelatives(selection, allDescendents=True, fullPath=True, type='transform') or []
    transforms.extend(x for x in selection if mc.nodeType(x) == 'transform')

    for transform in transforms:
        scene.add_object(Object(transform))
    scene.finalize_graph()
    
    for i, total, path, obj in scene.iter_dump():
        mc.progressWindow(e=True, progress=int(100 * i / total), status=obj.transform.split('|')[-1])
        if mc.progressWindow(q=True, isCancelled=True):
            break

    mc.progressWindow(endProgress=True)


def load():

    path = mc.fileDialog2(dialogStyle=1, fileMode=2)
    path = path and path[0]
    if not path:
        return

    mc.progressWindow(
        title='Geo.D Import',
        status='Initializing...',
        progress=0,
        isInterruptable=True,
    )

    scene = Scene(path, object_class=Object)
    
    for i, total, path, obj in scene.iter_load():
        mc.progressWindow(e=True, progress=int(100 * i / total), status=obj.transform.split('|')[-1])
        if mc.progressWindow(q=True, isCancelled=True):
            break

    mc.progressWindow(endProgress=True)
