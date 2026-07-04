"""Print APP_VERSION from constants.py without the leading v prefix."""
import re, sys, os

constants_path = os.path.join(os.path.dirname(__file__), 'src', 'constants.py')
with open(constants_path, 'r', encoding='utf-8') as f:
    for line in f:
        m = re.match(r"APP_VERSION\s*=\s*['\"]v?([^'\"]+)['\"]", line)
        if m:
            print(m.group(1))
            sys.exit(0)

print("0.0.0", file=sys.stderr)
sys.exit(1)
