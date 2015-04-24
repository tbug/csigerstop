import collections


class LRUCache(object):
    def __init__(self, capacity):
        self.max_capacity = capacity
        self.current_capacity = 0
        self.cache = collections.OrderedDict()

    def get(self, key):
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        else:
            return None

    def set(self, key, value):
        new_value_length = len(value)
        try:
            popped = self.cache.pop(key)
            self.current_capacity -= len(popped[1])
        except KeyError:
            # if the new key's size will increase to over max capacity,
            # pop item from cache
            if self.current_capacity + new_value_length > self.max_capacity:
                popped = self.cache.popitem(last=False)
                self.current_capacity -= len(popped[1])
        self.current_capacity += new_value_length
        self.cache[key] = value

    def get_keys(self):
        return (x for x in self.cache.keys())


if __name__ == "__main__":
    import random
    item = bytearray(random.getrandbits(8) for _ in range(1024*1))
    item_length = len(item)

    c = LRUCache(item_length*3)

    c.set("a", item)
    assert c.current_capacity == item_length
    c.set("b", item)
    assert c.current_capacity == item_length * 2
    c.set("c", item)
    assert c.current_capacity == item_length * 3
    c.set("d", item)
    assert c.current_capacity == item_length * 3
    c.set("e", item)
    assert c.current_capacity == item_length * 3

    assert c.get("a") is None  # both a and b should be empty
    assert c.get("b") is None  #

    assert c.get("c") == item  # c should still be there

    c.set("f", item)  # and since we accessed c, this `set` should push "d" out

    assert c.get("c") == item  # check that c is still there
