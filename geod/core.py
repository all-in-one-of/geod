import datetime
import errno
import json
import os

from geod.utils import makedirs


class BaseDumper(object):

    def __init__(self, root):
        self.root = os.path.abspath(root)

    def abspath(self, path):
        return os.path.join(self.root, os.path.normpath(path).lstrip('/'))

    def dump_meta(self, path, **obj):
        path = self.abspath(path) + '.json'
        makedirs(os.path.dirname(path))
        with open(path, 'w') as fh:
            json.dump(obj, fh, indent=4, sort_keys=True)

    def iter_objects(self):
        """Yield kwargs for other methods; only "name" is required."""
        raise NotImplementedError()

    def dump(self):
        for obj in self.iter_objects():
            obj.setdefault('path', obj['name'])
            obj['created_at'] = datetime.datetime.utcnow().isoformat()
            self.dump_geo(**obj)
            self.dump_meta(**obj)

    def dump_geo(self, **kw):
        pass
