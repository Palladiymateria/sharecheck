import argparse
import json
from pathlib import Path
import sys
from .scanner import scan
from .report import html_report


def main():
    parser = argparse.ArgumentParser(description="Check a local folder before publishing. No uploads; no source modifications.")
    parser.add_argument("folder", nargs="?", default=".", help="Folder to scan (default: current directory)")
    parser.add_argument("--json", action="store_true", help="Print machine-readable results")
    parser.add_argument("--html", type=Path, help="Write a standalone HTML report (new file only)")
    args = parser.parse_args()
    try:
        result = scan(args.folder)
        if args.html:
            with args.html.open("x", encoding="utf-8") as output:
                output.write(html_report(result))
    except (ValueError, OSError) as error:
        print(f"ShareCheck: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=True))
    else:
        print(f'SHARECHECK | {result["stats"]["files"]} files | {len(result["findings"])} findings')
        for finding in result["findings"]:
            location = finding["path"] + (f':{finding["line"]}' if finding["line"] else "")
            print(f'[{finding["severity"].upper()}] {location} - {finding["title"]}')
            print(f'  {finding["advice"]}')
        print("Coverage: UTF-8 text <=2 MiB; no Git history or dependency folders. Use --json for scan counts.")
    return 1 if any(f["severity"] in {"error", "warning"} for f in result["findings"]) else 0


if __name__ == "__main__":
    sys.exit(main())
