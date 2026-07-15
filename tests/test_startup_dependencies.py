import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import main
from utils import dependency_checker
from utils.dependency_checker import DependencySpec, check_startup_dependencies


class StartupDependencyTests(unittest.TestCase):
    def test_python_ytdlp_is_not_a_startup_dependency(self):
        packages = {dependency.package for dependency in dependency_checker.REQUIRED_DEPENDENCIES}

        self.assertNotIn("yt-dlp", packages)

    def test_main_defers_qt_widget_import_until_dependency_check(self):
        self.assertIsNone(main.QApplication)
        self.assertIsNone(main.QDialog)

    def test_reports_all_missing_required_dependencies(self):
        required = (
            DependencySpec("present_module", "present-package"),
            DependencySpec("missing_one", "missing-one"),
            DependencySpec("missing_two", "missing-two"),
        )

        def fake_available(module_name):
            return module_name == "present_module"

        with patch.object(dependency_checker, "is_module_available", side_effect=fake_available):
            report = check_startup_dependencies(
                required_dependencies=required,
                optional_dependencies=(),
                include_optional=False,
            )

        self.assertFalse(report.ok)
        self.assertEqual(report.format_missing_required(), "missing-one, missing-two")

    def test_optional_dependency_does_not_fail_startup(self):
        required = (DependencySpec("present_module", "present-package"),)
        optional = (DependencySpec("missing_optional", "optional-package", required=False),)

        def fake_available(module_name):
            return module_name == "present_module"

        with patch.object(dependency_checker, "is_module_available", side_effect=fake_available):
            report = check_startup_dependencies(
                required_dependencies=required,
                optional_dependencies=optional,
                include_optional=True,
            )

        self.assertTrue(report.ok)
        self.assertEqual(report.format_missing_optional(), "optional-package")


if __name__ == "__main__":
    unittest.main()
