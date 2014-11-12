import bpy

from ..scene import Scene
from .object import BlenderObject as Object


def dump():
    scene = Scene('/Users/mikeboers/Desktop/test.geod', object_class=Object)
    for node in bpy.context.selected_objects:
        if node.data and node.type != "MESH":
            continue
        scene.add_object(Object(node))
    scene.finalize_graph()
    scene.dump()

