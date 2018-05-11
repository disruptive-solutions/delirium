import time

from .cache import CacheObject


class CacheDictionary(CacheObject):
    def __init__(self, addr_range, duration):
        super(CacheDictionary, self).__init__(addr_range, duration)
        self._data = {}

    def add_record(self, label):
        rec = self._data.get(label, {})

        if not rec:
            rec['addr'] = self._n_generator.next()

        rec['time'] = time.time()
        self._data.update({label: rec})

    def close(self):
        pass

    def get_addr_by_name(self, value):
        return [self._data.get(value).get('addr')]

    def get_name_by_addr(self, value):
        out = []
        for k, v in self._data.items():
            if v['addr'] == value:
                out.append(k)
        return out

    def prune_stale(self):
        to_del = []

        for k, v in self._data.items():
            if v['time'] <= time.time() - self._duration:
                to_del.append(k)

        for k in to_del:
            del self._data[k]
