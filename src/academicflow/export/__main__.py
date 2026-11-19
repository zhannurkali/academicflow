"""Command line: ``python -m academicflow.export paper.ipynb paper.docx``."""
from __future__ import annotations

import argparse

from academicflow.export import export_notebook, infer_format


def main(argv: list[str] | None = None) -> int:
    """Run the exporter. Returns a process exit code."""
    parser = argparse.ArgumentParser(prog="python -m academicflow.export")
    parser.add_argument("notebook")
    parser.add_argument("output")
    parser.add_argument("--format", choices=["docx", "latex", "md"])
    parser.add_argument("--style", default="apa", choices=["apa", "ieee", "nature"])
    parser.add_argument("--bib")
    args = parser.parse_args(argv)
    fmt = args.format or infer_format(args.output)
    print(export_notebook(args.notebook, args.output, fmt, args.style, args.bib))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
