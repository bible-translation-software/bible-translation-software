import os
import pyflakes.api
import subprocess
import unittest

try:
    _eslint_installed = subprocess.run(["eslint", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
except FileNotFoundError:
    _eslint_installed = False

try:
    _npm_installed = subprocess.run(["which", "npm"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
except FileNotFoundError:
    _npm_installed = False


class CodeLinting(unittest.TestCase):

    def test_pyflakes(self):
        source_files = subprocess.check_output(["git", "ls-files", "-z"]).split(b"\0")
        source_files = [x.decode("UTF-8") for x in source_files]
        for source_file in source_files:
            parts = source_file.split("/")
            if len(parts) >= 2 and parts[1] == "migrations":
                pass # skip automatically generate migrations files
            elif source_file.endswith(".py") and os.path.exists(source_file):
                with open(source_file, encoding="UTF-8") as f:
                    content = f.read()
                warnings = pyflakes.api.check(content, source_file)
                with self.subTest(source_file=source_file):
                    self.assertEqual(warnings, 0, "Expected no warnings in %s" % source_file)

    @unittest.skipIf(not _eslint_installed, "eslint not installed")
    def test_eslint(self):
        source_files = subprocess.check_output(["git", "ls-files", "-z"]).split(b"\0")
        source_files = [x.decode("UTF-8") for x in source_files]
        for source_file in source_files:
            if os.path.basename(source_file) in ["dialog-polyfill.js", "autotrack.js"]:
                continue
            if source_file.endswith(".min.js"):
                continue
            if source_file.startswith(os.path.join("biblets", "static", "uikit/")):
                continue
            if source_file.startswith("jstest" + os.path.sep):
                continue
            if source_file.endswith(".js") and os.path.exists(source_file):
                cp = subprocess.run(["eslint", "--quiet", source_file])
                with self.subTest(source_file=source_file):
                    self.assertEqual(cp.returncode, 0, "Expected no eslint errors in %s" % source_file)

    @unittest.skipIf(not _npm_installed, "npm not installed")
    def test_npm_test(self):
        subprocess.check_output(["npm", "test"])

    def test_po(self):
        locale_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "locale")
        for dirname in os.listdir(locale_path):
            if not os.path.isdir(os.path.join(locale_path, dirname)):
                continue
            pofilename = os.path.join(locale_path, dirname, "LC_MESSAGES/django.po")
            output = subprocess.check_output(["msggrep", "-v", "-T", "-e", ".", pofilename])
            self.assertEqual(output, b"", "Check that no untranslated strings remain in pofilename")

class DepedencyChecks(unittest.TestCase):

    def test_pip_check(self):
        cp = subprocess.run(["pip", "check", "--quiet"])
        if cp.returncode != 0:
            subprocess.run(["pip", "check"])
        self.assertEqual(cp.returncode, 0, "pip check should return 0 exit code")
