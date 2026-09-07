"""`aziz export` -- option A de l'analyse de faisabilité (voir robin-analysis.md).

Export NDJSON streaming par ressource, sans changement serveur. Le
`ResourceProvider` est le point d'extension vers la vraie API paginée du CLI ;
`LocalJSONProvider` sert de source de données de démonstration/test.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, Optional

SCHEMA_VERSION = "1"

REDACTED = "***REDACTED***"
SECRET_KEYS = {"token", "secret", "password", "webhook", "webhook_url", "api_key", "access_token"}


class ResourceProvider:
    """Source de données paginée pour une ressource métier."""

    def list_resources(self) -> list[str]:
        raise NotImplementedError

    def iter_records(self, resource: str) -> Iterator[dict]:
        raise NotImplementedError


class LocalJSONProvider(ResourceProvider):
    """Lit des pages JSON depuis <root>/<resource>/*.json (une page = une liste d'enregistrements)."""

    def __init__(self, root: Path):
        self.root = Path(root)

    def list_resources(self) -> list[str]:
        if not self.root.exists():
            return []
        return sorted(p.name for p in self.root.iterdir() if p.is_dir())

    def iter_records(self, resource: str) -> Iterator[dict]:
        resource_dir = self.root / resource
        if not resource_dir.exists():
            raise FileNotFoundError(f"unknown resource: {resource}")
        for page_file in sorted(resource_dir.glob("*.json")):
            page = json.loads(page_file.read_text())
            for record in page:
                yield record


def redact(value):
    """Masque récursivement les clés qui ressemblent à des secrets (jetons, webhooks...)."""
    if isinstance(value, dict):
        return {
            key: (REDACTED if key.lower() in SECRET_KEYS else redact(val))
            for key, val in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


@dataclass
class ExportResult:
    resource: str
    record_count: int
    ok: bool
    error: Optional[str] = None


def export_resource(provider: ResourceProvider, resource: str, out_path: Path, dry_run: bool) -> ExportResult:
    try:
        records = sorted(provider.iter_records(resource), key=lambda r: r["id"])
    except Exception as exc:
        return ExportResult(resource=resource, record_count=0, ok=False, error=str(exc))

    if dry_run:
        return ExportResult(resource=resource, record_count=len(records), ok=True)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        for record in records:
            f.write(json.dumps(redact(record), sort_keys=True))
            f.write("\n")
    return ExportResult(resource=resource, record_count=len(records), ok=True)


def run_export(
    provider: ResourceProvider, resources: Iterable[str], out_dir: Path, dry_run: bool
) -> tuple[list[ExportResult], dict]:
    resources = list(resources)
    results = [
        export_resource(provider, resource, out_dir / f"{resource}.ndjson", dry_run)
        for resource in resources
    ]

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": resources,
        "resources": {
            r.resource: {"record_count": r.record_count, "ok": r.ok, "error": r.error}
            for r in results
        },
    }

    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))

    return results, manifest


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aziz export")
    parser.add_argument(
        "--resource",
        action="append",
        dest="resources",
        help="ressource à exporter (répétable) ; défaut : toutes les ressources connues",
    )
    parser.add_argument("--format", choices=["ndjson"], default="ndjson")
    parser.add_argument(
        "--data-root",
        default="data",
        help="racine locale simulant l'API de lecture paginée (LocalJSONProvider)",
    )
    parser.add_argument("--out-dir", default="export-out")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv=None) -> int:
    args = build_arg_parser().parse_args(argv)
    provider = LocalJSONProvider(Path(args.data_root))
    resources = args.resources or provider.list_resources()

    if not resources:
        print("no resource to export", file=sys.stderr)
        return 1

    results, _manifest = run_export(provider, resources, Path(args.out_dir), args.dry_run)

    for r in results:
        status = "ok" if r.ok else f"FAILED ({r.error})"
        print(f"{r.resource}: {r.record_count} records - {status}")

    if args.dry_run:
        print(f"dry-run: would write to {args.out_dir}/")

    return 0 if all(r.ok for r in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
