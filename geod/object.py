
class BaseObject(object):

    @classmethod
    def from_meta(cls, meta, parent):
        return cls(meta['name'])

    def __init__(self, name):
        self.name = name
        self.children = None

    def __repr__(self):
        return '<geod.%s %r at %r>' % (
            self.__class__.__name__,
            self.name,
            self.guid
        )

    @property
    def guid(self):
        return id(self)

    def _iter_child_args(self):
        raise NotImplementedError()

    def _init_graph(self, scene):

        # Stop from processing this node again.
        if self.children is not None:
            return

        self.children = []
        for args in self._iter_child_args():
            child = self.__class__(*args)
            child = scene.add_object(child)
            self.children.append(child)
            child._init_graph(scene)

    def get_basic_meta(self):
        return {
            'name': self.name,
        }

    def get_transforms(self):
        raise NotImplementedError()

    def export_geo(self, base):
        raise NotImplementedError()


