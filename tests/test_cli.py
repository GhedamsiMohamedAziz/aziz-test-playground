import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def run_cli(args, cwd):
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    return subprocess.run(
        [sys.executable, "-m", "aziz", "export", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
    )


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cwd = Path(self.tmp.name)
        tasks_dir = self.cwd / "data" / "tasks"
        tasks_dir.mkdir(parents=True)
        (tasks_dir / "page1.json").write_text(json.dumps([{"id": 2}, {"id": 1}]))

    def test_export_writes_ndjson_and_exits_zero(self):
        result = run_cli(["--resource", "tasks"], cwd=self.cwd)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.cwd / "export-out" / "tasks.ndjson").exists())
        self.assertTrue((self.cwd / "export-out" / "manifest.json").exists())

    def test_dry_run_exits_zero_without_writing(self):
        result = run_cli(["--resource", "tasks", "--dry-run"], cwd=self.cwd)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.cwd / "export-out").exists())

    def test_missing_resource_exits_nonzero(self):
        result = run_cli(["--resource", "ghost"], cwd=self.cwd)

        self.assertEqual(result.returncode, 2)
        self.assertIn("FAILED", result.stdout)

    def test_no_resource_available_exits_one(self):
        with tempfile.TemporaryDirectory() as empty_cwd:
            result = run_cli([], cwd=empty_cwd)  # pas de dossier data/ ici

        self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main()
