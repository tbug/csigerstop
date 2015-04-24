import collections


class LRUCache(object):
    def __init__(self, capacity):
        self.max_capacity = capacity
        self.current_capacity = 0
        self.cache = collections.OrderedDict()

    def get(self, key):
        try:
            value = self.cache.pop(key)
            self.cache[key] = value
            return value
        except KeyError:
            return None

    def set(self, key, value):
        new_value_length = len(value)
        try:
            popped = self.cache.pop(key)
            self.current_capacity -= len(popped)
        except KeyError:
            if self.current_capacity + new_value_length > self.max_capacity:
                popped = self.cache.popitem(last=False)
                self.current_capacity -= len(popped)
        self.current_capacity += new_value_length
        self.cache[key] = value

    def get_keys(self):
        return self.cache.keys()
