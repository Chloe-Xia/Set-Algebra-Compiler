"""Self-contained smoke tests for the unmodified course implementation."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_FILES = [
    "main.py", "lexer.py", "parser.py", "type_checker.py",
    "evaluation.py", "SLR Parsing Table.csv",
]


class CompilerSmokeTests(unittest.TestCase):
    def run_source(self, source):
        # Isolate generated JSON so running tests never overwrites repository files.
        with tempfile.TemporaryDirectory() as temporary:
            workdir = Path(temporary)
            for filename in RUNTIME_FILES:
                shutil.copy2(ROOT / filename, workdir / filename)
            (workdir / "input.set").write_text(source, encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, "main.py", "input.set"],
                cwd=workdir,
                text=True,
                capture_output=True,
                timeout=15,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            output_file = workdir / "evaluation_out.json"
            self.assertTrue(output_file.exists(), completed.stdout)
            result = json.loads(output_file.read_text(encoding="utf-8"))
            return result.get("value")

    def test_variable_arithmetic(self):
        self.assertEqual(self.run_source("let int a be 3 . let int b be 4 . show a + b ."), "7")

    def test_operator_precedence(self):
        self.assertEqual(self.run_source("show 1 + 2 * 3 ."), "7")

    def test_boolean_comparison(self):
        self.assertEqual(self.run_source("show 3 > 2 ."), "true")

    def test_symbolic_set_union(self):
        self.assertEqual(self.run_source("show { x : x > 3 } U { x : x < 1 } ."), "{ x: x > 3 } U { x: x < 1 }")

    def test_set_membership(self):
        self.assertEqual(self.run_source("let set s be { x : x > 3 } . show 5 @ s ."), "true")


if __name__ == "__main__":
    unittest.main()
