"""Stream build subprocess output to both the console and its UTF-8 log."""
import subprocess


def run_logged(command, *, stdout, check=False, **kwargs):
    with subprocess.Popen(command, stdout=subprocess.PIPE, text=True,
                          encoding='utf-8', errors='replace', bufsize=1, **kwargs) as process:
        for line in process.stdout:
            stdout.write(line)
            stdout.flush()
            print(line, end='', flush=True)
        returncode = process.wait()
    if check and returncode:
        raise subprocess.CalledProcessError(returncode, command)
    return subprocess.CompletedProcess(command, returncode)
