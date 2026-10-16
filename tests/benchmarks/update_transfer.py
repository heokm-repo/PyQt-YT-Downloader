"""Offline byte identity, callback and response-lifetime comparison for S7."""
import argparse
import hashlib
import inspect
from pathlib import Path
import statistics
import sys
import time
from unittest.mock import patch

from .environment import ROOT, prepare_run, environment_manifest, file_manifest, write_json


class Response:
    def __init__(self, data, known=True):
        self.data = data
        self.headers = {'content-length': str(len(data))} if known else {}
        self.closed = 0
        self.chunks_read = 0
        self.cancel_requested_at = None

    def raise_for_status(self):
        pass

    def close(self):
        self.closed += 1

    def iter_content(self, chunk_size):
        for offset in range(0, len(self.data), chunk_size):
            self.chunks_read += 1
            if self.chunks_read == 10:
                self.cancel_requested_at = time.perf_counter()
            yield self.data[offset:offset+chunk_size]


def cancellation_probe(app_updater, download_stream, output, known):
    """Time local handling after intent at chunk 10, excluding socket/UI wait."""
    data = b'x' * (1024*1024)
    digest = 'sha256:' + hashlib.sha256(data).hexdigest()
    samples = []
    for repeat in range(21):  # One warm-up, then 20 samples per header mode.
        response = Response(data, known)
        kwargs = {}
        if 'check_cancel' in inspect.signature(app_updater.download_update).parameters:
            kwargs['check_cancel'] = lambda: response.chunks_read >= 10

        def progress(_):
            if response.chunks_read >= 10:
                raise RuntimeError('cancel fixture')

        with patch.object(download_stream.requests, 'get', return_value=response), patch.object(
            app_updater, 'update_temp_dir', return_value=str(output)
        ):
            result = app_updater.download_update('offline', progress, digest, **kwargs)
            finished = time.perf_counter()
        sample = {'cancelled': result is None, 'chunks': response.chunks_read,
                  'response_close': response.closed,
                  'file_exists': (output/app_updater.UPDATE_TEMP_FILENAME).exists(),
                  'intent_to_return_ms': (finished-response.cancel_requested_at)*1000}
        if repeat:
            samples.append(sample)
    timings = [sample['intent_to_return_ms'] for sample in samples]
    return {'mode': 'app_cancel', 'known_length': known, 'samples': samples,
            'intent_to_return_ms': {'median': statistics.median(timings),
                                    'min': min(timings), 'max': max(timings)}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source', type=Path, default=ROOT/'src')
    args = parser.parse_args()
    output = prepare_run(args.output)
    sys.path.insert(0, str(args.source.resolve()))
    write_json(output/'environment.json', environment_manifest())
    from utils import app_updater, download_stream
    from gui.dialogs.download_progress_dialog import DownloadWorker
    results = {'source_files': file_manifest(args.source, suffixes={'.py'}), 'cases': []}
    for size in (1024*1024, 8*1024*1024):
        data = bytes(range(256)) * (size//256)
        digest = hashlib.sha256(data).hexdigest()
        for mode in ('binary_raw', 'binary_ui', 'app'):
            response = Response(data)
            callbacks = []
            path = output / f'{mode}-{size}.bin'
            with patch.object(download_stream.requests, 'get', return_value=response):
                if mode == 'app':
                    with patch.object(app_updater, 'update_temp_dir', return_value=str(output)):
                        path = Path(app_updater.download_update('offline', callbacks.append, 'sha256:'+digest))
                elif mode == 'binary_raw':
                    assert download_stream.download_file('offline', str(path), lambda *args: callbacks.append(args))
                else:
                    worker = DownloadWorker()
                    worker.progress.connect(lambda *args: callbacks.append(args))

                    def download(progress, cancel, binary_names=None):
                        return download_stream.download_file('offline', str(path), lambda *args: progress('fixture', *args), cancel)

                    with patch('utils.bin.manager.download_initial_binaries', side_effect=download):
                        worker.run()
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            assert actual == digest
            results['cases'].append({'mode': mode, 'bytes': size, 'chunks': response.chunks_read,
                                     'callbacks': len(callbacks), 'last_callback': callbacks[-1] if callbacks else None,
                                     'response_close': response.closed, 'sha256': actual})
    for known in (True, False):
        results['cases'].append(cancellation_probe(app_updater, download_stream, output, known))
    write_json(output/'results.json', results)
    print(output/'results.json')


if __name__ == '__main__':
    main()
