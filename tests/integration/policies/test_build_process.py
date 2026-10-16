"""Build logs remain visible and failures preserve their subprocess exit code."""
import io
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from build_scripts.build_process import run_logged


@pytest.mark.parametrize('exit_code', [0, 7])
def test_child_output_reaches_console_and_log_with_correct_exit_code(capsys, exit_code):
    log = io.StringIO()
    command = [sys.executable, '-u', '-c',
               "import sys; print('stdout message'); print('stderr message', file=sys.stderr); sys.exit(int(sys.argv[1]))",
               str(exit_code)]
    if exit_code:
        with pytest.raises(subprocess.CalledProcessError) as error:
            run_logged(command, stdout=log, stderr=subprocess.STDOUT, check=True)
        assert error.value.returncode == exit_code
    else:
        assert run_logged(command, stdout=log, stderr=subprocess.STDOUT, check=True).returncode == 0
    console = capsys.readouterr().out
    assert console == log.getvalue()
    assert 'stdout message' in console and 'stderr message' in console
