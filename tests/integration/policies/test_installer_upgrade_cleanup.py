import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
INSTALLER_SCRIPT = ROOT / "installer.iss"


def read_installer_section(section_name):
    section_header = f"[{section_name}]".casefold()
    section_lines = []
    in_section = False

    for raw_line in INSTALLER_SCRIPT.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("[") and line.endswith("]"):
            if in_section:
                break
            in_section = line.casefold() == section_header
            continue
        if in_section and line and not line.startswith(";"):
            section_lines.append(line)

    return section_lines


class InstallerUpgradeCleanupTests(unittest.TestCase):
    def test_installer_has_install_delete_section(self):
        self.assertTrue(
            read_installer_section("InstallDelete"),
            "installer.iss must define a non-empty [InstallDelete] section",
        )

    def test_installer_removes_previous_pyinstaller_runtime(self):
        cleanup_rule = re.compile(
            r'^Type:\s*filesandordirs\s*;\s*Name:\s*"\{app\}\\_internal"\s*$',
            re.IGNORECASE,
        )

        self.assertTrue(
            any(
                cleanup_rule.fullmatch(line)
                for line in read_installer_section("InstallDelete")
            ),
            "updates must remove the previous {app}\\_internal runtime",
        )


if __name__ == "__main__":
    unittest.main()
