import copy
import json
import os
import pprint

from .utils import makedirs
from .object import BaseObject


class Scene(object):

    object_class = BaseObject

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

    def load(self):

        # Load all of the objects, and establish relationships.
        path_to_meta = {}
        for dir_path, dir_names, file_names in os.walk(self.path):
            for file_name in file_names:
                if not file_name.endswith('.json'):
                    continue

                path = os.path.join(dir_path, file_name)
                with open(path) as fh:
                    meta = json.load(fh)
                meta = self._deep_encode(meta)

                meta['_filepath'] = path
                meta['_path'] = os.path.relpath(os.path.splitext(path)[0], self.path)
                path_to_meta[meta['_path']] = meta

                meta['_children'] = []
                meta['_parent'] = path_to_meta.get(os.path.dirname(meta['_path']))
                if meta['_parent']:
                    meta['_parent']['_children'].append(meta)

        # Break up combo subnet/geometry/instance nodes (as geometryis not
        # allowed to have children (by Houdini, and us)).
        for meta in path_to_meta.values():

            if meta.get('_children') and meta.get('geometry'):

                geo = copy.deepcopy(meta)
                geo.pop('transform', None)

                geo['_path'] = os.path.join(geo['_path'], geo['name'])
                path_to_meta[geo['_path']] = geo
                geo['_children'] = []
                geo['_parent'] = meta
                meta['_children'].append(geo)

                meta.pop('geometry', None)


        # Get the root nodes.
        root_paths = set(path_to_meta)
        for meta in path_to_meta.itervalues():
            for child in meta['_children']:
                try:
                    root_paths.remove(child['_path'])
                except KeyError:
                    pass

        # Create all of the nodes in the right order.
        to_visit = [path_to_meta[path] for path in sorted(root_paths)]
        visited = set()
        while to_visit:
            meta = to_visit.pop(0)
            if meta['_path'] in visited:
                continue
            visited.add(meta['_path'])

            obj = self.object_class.from_meta(meta, (meta.get('_parent') or {}).get('_object'))
            meta['_object'] = obj
            obj._meta = meta
            self.add_object(obj)

            to_visit.extend(meta['_children'])

        # Re-establish the heirarchy.
        self.finalize_graph()

        # Restore transforms and load geometry.
        for _, obj in self.walk():

            transforms = obj._meta.get('transform')
            if transforms:
                obj.set_transforms(transforms)

            geometry = obj._meta.get('geometry')
            if geometry:
                path = geometry.get('path')
                if path:
                    geometry['path'] = os.path.join(os.path.dirname(obj._meta['_filepath']), path)
                obj.import_geo(geometry)







    def _deep_encode(self, x):
        if isinstance(x, dict):
            return dict((self._deep_encode(k), self._deep_encode(v)) for k, v in x.iteritems())
        elif isinstance(x, list):
            return [self._deep_encode(y) for y in x]
        elif isinstance(x, unicode):
            return x.encode('ascii')
        else:
            return x





