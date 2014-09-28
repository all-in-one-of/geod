import datetime
import errno
import json
import os

from geod.utils import makedirs


class BaseCommon(object):

    def __init__(self, root):
        self.root = os.path.abspath(root)

    def abspath(self, path):
        return os.path.join(self.root, os.path.normpath(path).lstrip('/'))


class BaseDumper(BaseCommon):

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
            self.dump_meta(**obj)
            self.dump_geo(**obj)

    def dump_geo(self, **kw):
        pass


class BaseLoader(BaseCommon):

    def iter_objects(self):
        for dir_path, dir_names, file_names in os.walk(self.root):
            for file_name in file_names:
                if file_name.startswith('.') or not file_name.endswith('.json'):
                    continue
                path = os.path.join(dir_path, file_name)
                with open(path) as fh:
                    obj = json.load(fh)
                obj['path'] = os.path.relpath(os.path.splitext(path)[0], self.root)
                yield obj

    def load(self):
        for obj in self.iter_objects():
            self.load_object(**obj)

    def load_object(self, **kw):
        pass
