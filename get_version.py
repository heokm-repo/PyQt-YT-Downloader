"""Print the validated version without importing the application."""
import sys
from build_scripts.release_inputs import read_version

if __name__ == '__main__':
    try:
        print(read_version())
    except (OSError, ValueError, SyntaxError) as exc:
        print(f'Cannot read application version: {exc}', file=sys.stderr)
        raise SystemExit(1)
