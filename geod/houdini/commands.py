import hou

#from .dumper import HoudiniDumper
#from .loader import HoudiniLoader
from .scene import HoudiniScene as Scene
from .object import HoudiniObject as Object


def dump():
    scene = Scene('/Users/mikeboers/Desktop/test.geod')
    for node in hou.selectedNodes():
        scene.add_object(Object(node))
    scene.finalize_graph()
    scene.dump()


def load():    
    scene = Scene('/Users/mikeboers/Desktop/test.geod')
    scene.load()
