"""Compare the prior linear ID lookup with the ordered collection index."""
import sys

from .fixtures import task_records
from .measurements import measure


def benchmark_task_lookup(settings, repeats):
    from data.duplicate_checker import active_duplicate_keys
    from data.models import DownloadTask
    from data.task_collection import TaskCollection

    results = []
    for size in (10, 100, 1000):
        tasks = [DownloadTask.from_dict(record) for record in task_records(size, settings)]
        collection = TaskCollection(tasks)
        ids = [task.id for task in tasks] + [-1]

        def linear():
            matches = [next((task for task in tasks if task.id == task_id), None) for task_id in ids]
            assert matches == tasks + [None]
            return len(matches)

        def indexed():
            matches = [collection.get(task_id) for task_id in ids]
            assert matches == tasks + [None]
            return len(matches)

        active = active_duplicate_keys(tasks)
        results.append({
            'tasks': size, 'lookups_per_sample': len(ids),
            'linear': measure(linear, repeats), 'indexed': measure(indexed, repeats),
            'list_shallow_bytes': sys.getsizeof(tasks),
            'index_shallow_bytes': sys.getsizeof(collection._by_id),
            'active_keys': len(active),
            'active_set_and_tuple_bytes': sys.getsizeof(active) + sum(map(sys.getsizeof, active)),
            'memory_note': 'Python shallow container sizes only; excludes shared tasks, IDs and strings',
        })
    return results
