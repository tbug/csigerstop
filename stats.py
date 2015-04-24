import collections
import time


def hackernews_score(number, hour_age, gravity=1.2):
    return (number - 1) / pow((hour_age+2), gravity)


class StatsObject(object):
    def __init__(self, purge_after=900):
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

    def get_top(self, n):
        scoregen = ((key, hackernews_score(count, (last - first) / 3600))
                    for (key, (first, last, count)) in self.data.items())
        return reversed(
            list(
                map(
                    lambda t: t[0], sorted(
                        scoregen, key=lambda t: t[1])[:n])))
