import collections
import time
from math import log, exp


def hotness(count, last, now):
    base = log(max(count, 1))
    diff = (now - last) / 604800
    x = diff - 1
    return base * exp(-8*x*x)


class StatsObject(object):
    def __init__(self, purge_after=900, min_count=5):
        self.purge_after = purge_after
        self.min_count = min_count
        self.data = {}

    def increment(self, key):
        if key in self.data:
            current = self.data[key]
            self.data[key] = (current[0], time.time(), current[2]+1)
        else:
            now = time.time()
            self.data[key] = (now, now, 2)

    def clean(self):
        now = time.time()
        purge_after = self.purge_after
        min_count = self.min_count
        self.data = {key: value
                     for key, value in self.data.items()
                     if (now - value[1]) < purge_after and value[2] >= min_count}

    def get_top(self, n):
        now = time.time()
        scoregen = ((key, hotness(count, first, now))
                    for (key, (first, last, count)) in self.data.items())
        sort = sorted(scoregen, key=lambda t: t[1])[:n]
        return list(reversed(list(map(lambda t: t[0], sort))))
