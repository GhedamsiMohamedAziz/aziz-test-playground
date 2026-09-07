import sys

from aziz.export import main as export_main


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] != "export":
        print("usage: aziz export [options]", file=sys.stderr)
        return 1
    return export_main(argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
