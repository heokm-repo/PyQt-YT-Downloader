"""constants.py에서 APP_VERSION을 읽어 숫자만 출력하는 스크립트"""
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
