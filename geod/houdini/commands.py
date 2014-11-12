import hou

from ..scene import Scene
from .object import HoudiniObject as Object


def dump():
    scene = Scene('/Users/mikeboers/Desktop/test.geod', object_class=Object)
    for node in hou.selectedNodes():
        scene.add_object(Object(node))
    scene.finalize_graph()
    scene.dump()


def load():    
    scene = Scene('/Users/mikeboers/Desktop/test.geod', object_class=Object)
    scene.load()
