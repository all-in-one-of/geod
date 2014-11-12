
Blender
-------

import sys

root = '/Volumes/heap/sitg/dev'
for pkg in ('metatools', 'geod'):
    path = root + '/' + pkg
    if path not in sys.path:
        sys.path.append(path)

for obj in D.objects:
    obj.select = not (obj.data and obj.type != 'MESH')

from metatools.imports import autoreload
import geod.blender.commands

autoreload(geod.blender.commands); geod.blender.commands.dump()

