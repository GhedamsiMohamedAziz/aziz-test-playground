import json
import tempfile
import unittest
from pathlib import Path

from aziz.export import LocalJSONProvider, redact, run_export


def write_page(root: Path, resource: str, filename: str, records) -> None:
    resource_dir = root / resource
    resource_dir.mkdir(parents=True, exist_ok=True)
    (resource_dir / filename).write_text(json.dumps(records))


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data_root = Path(self.tmp.name) / "data"
        self.out_dir = Path(self.tmp.name) / "out"

    def test_exports_sorted_ndjson_by_id_across_pages(self):
        write_page(self.data_root, "tasks", "page1.json", [{"id": 3, "title": "c"}])
        write_page(self.data_root, "tasks", "page2.json", [{"id": 1, "title": "a"}, {"id": 2, "title": "b"}])
        provider = LocalJSONProvider(self.data_root)

        results, _manifest = run_export(provider, ["tasks"], self.out_dir, dry_run=False)

        lines = (self.out_dir / "tasks.ndjson").read_text().splitlines()
        ids = [json.loads(line)["id"] for line in lines]
        self.assertEqual(ids, [1, 2, 3])
        self.assertTrue(results[0].ok)
        self.assertEqual(results[0].record_count, 3)

    def test_manifest_records_scope_and_counts(self):
        write_page(self.data_root, "tasks", "page1.json", [{"id": 1}])
        write_page(self.data_root, "notes", "page1.json", [{"id": 1}, {"id": 2}])
        provider = LocalJSONProvider(self.data_root)

        _results, manifest = run_export(provider, ["tasks", "notes"], self.out_dir, dry_run=False)

        self.assertEqual(manifest["schema_version"], "1")
        self.assertEqual(manifest["scope"], ["tasks", "notes"])
        self.assertEqual(manifest["resources"]["tasks"]["record_count"], 1)
        self.assertEqual(manifest["resources"]["notes"]["record_count"], 2)
        on_disk = json.loads((self.out_dir / "manifest.json").read_text())
        self.assertEqual(on_disk, manifest)

    def test_redacts_secrets_recursively(self):
        record = {"id": 1, "token": "abc", "nested": {"webhook": "http://x"}, "title": "ok"}

        redacted = redact(record)

        self.assertEqual(redacted["token"], "***REDACTED***")
        self.assertEqual(redacted["nested"]["webhook"], "***REDACTED***")
        self.assertEqual(redacted["title"], "ok")

    def test_dry_run_writes_nothing_but_counts_records(self):
        write_page(self.data_root, "tasks", "page1.json", [{"id": 1}])
        provider = LocalJSONProvider(self.data_root)

        results, _manifest = run_export(provider, ["tasks"], self.out_dir, dry_run=True)

        self.assertFalse(self.out_dir.exists())
        self.assertEqual(results[0].record_count, 1)

    def test_unknown_resource_is_reported_as_partial_failure(self):
        provider = LocalJSONProvider(self.data_root)

        results, manifest = run_export(provider, ["ghost"], self.out_dir, dry_run=False)

        self.assertFalse(results[0].ok)
        self.assertIsNotNone(results[0].error)
        self.assertEqual(manifest["resources"]["ghost"]["ok"], False)


if __name__ == "__main__":
    unittest.main()
