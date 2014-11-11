import json
import os
import pprint

from .utils import makedirs


class Scene(object):

    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.guid_to_object = {}
        self.root_objects = None

    def _abspath(self, path):
        return os.path.join(self.path, os.path.normpath(path).lstrip('/'))

    def add_object(self, obj, graph=False):
        return self.guid_to_object.setdefault(obj.guid, obj)

    def finalize_graph(self):
        for obj in self.guid_to_object.values():
            obj._init_graph(self)
        root_guids = set(self.guid_to_object)
        for obj in self.guid_to_object.itervalues():
            for child in obj.children:
                try:
                    root_guids.remove(child.guid)
                except KeyError:
                    pass
        self.root_objects = [self.guid_to_object[guid] for guid in sorted(root_guids)]

    def walk(self):
        for root in self.root_objects:
            for x in self._walk(root, ''):
                yield x

    def _walk(self, obj, path):
        path = os.path.join(path, os.path.normpath(obj.name).replace('/', ''))
        yield path, obj
        for child in obj.children:
            for x in self._walk(child, path):
                yield x

    def dump(self):

        # First pass: setup all the basic information.
        for path, obj in self.walk():

            path = self._abspath(path)
            makedirs(os.path.dirname(path))

            meta = obj.get_basic_meta()
            meta['transform'] = obj.get_transforms()

            geo = obj.export_geo(path)
            if geo:
                if 'path' in geo:
                    geo['path'] = os.path.relpath(geo['path'], os.path.dirname(path))
                meta['geometry'] = geo

            with open(path + '.json', 'w') as fh:
                json.dump(meta, fh, indent=4, sort_keys=True)





