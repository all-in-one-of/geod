import datetime
import errno
import json
import os

from geod.utils import makedirs


class BaseLoader(BaseCommon):

    def iter_objects(self):
        self._objects = {}
        for dir_path, dir_names, file_names in os.walk(self.root):
            for file_name in file_names:

                if file_name.startswith('.') or not file_name.endswith('.json'):
                    continue

                path = os.path.join(dir_path, file_name)
                with open(path) as fh:
                    obj = json.load(fh)

                obj = self._encode(obj)

                obj['path'] = os.path.relpath(os.path.splitext(path)[0], self.root)

                # Establish relationships.
                self._objects[obj['path']] = obj
                obj['_parent'] = self._objects.get(os.path.dirname(obj['path']))

                yield obj

    def _encode(self, x):
        if isinstance(x, dict):
            return dict((self._encode(k), self._encode(v)) for k, v in x.iteritems())
        elif isinstance(x, list):
            return [self._encode(y) for y in x]
        elif isinstance(x, unicode):
            return x.encode('ascii')
        else:
            return x

    def load(self):
        for obj in self.iter_objects():
            self.load_object(obj)

    def load_object(self, obj):
        pass
