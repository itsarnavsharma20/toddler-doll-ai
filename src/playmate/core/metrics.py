"""Anonymous counters. Only counts by reply source (for example rhyme id). Never stores what a child said."""
import threading
from collections import Counter

_lock = threading.Lock()
_counts = Counter()


def record(source):
    with _lock:
        _counts[source] += 1


def snapshot():
    with _lock:
        return dict(_counts)
