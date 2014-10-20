
Blender
-------

import sys
from imp import reload

path = '/Volumes/heap/sitg/dev/geod'
if path not in sys.path:
    sys.path.append(path)

import geod.blender
reload(geod.core) and reload(geod.blender) and geod.blender.main_dump()

