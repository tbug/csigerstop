import collections
import time
from math import log, exp


def hotness(count, last, now):
    base = log(max(count, 1))
    diff = (now - last) / 3600
    x = diff - 1
    return base * exp(-8*x*x)


class StatsObject(object):
    def __init__(self, purge_after=7200):
        self.purge_after = purge_after
        self.data = {}

    def increment(self, key):
        if key in self.data:
            current = self.data[key]
            self.data[key] = (current[0], time.time(), current[2]+1)
        else:
            now = time.time()
            self.data[key] = (now, now, 1)

    def clean(self):
        now = time.time()
        purge_after = self.purge_after
        self.data = {key: value
                     for key, value in self.data.items()
                     if (now - value[1]) < purge_after}

    def get_top(self, n, min_count=1):
        now = time.time()
        scoregen = ((key, hotness(count, first, now))
                    for (key, (first, last, count)) in self.data.items() if count >= min_count)
        sort = sorted(scoregen, key=lambda t: t[1])[:n]
        return list(reversed(list(map(lambda t: t[0], sort))))
