from dataclasses import asdict, dataclass
from pathlib import Path
import os
import re


SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache"}
TEXT_LIMIT = 2 * 1024 * 1024
RULES = [
    ("Private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{40,})\b")),
    ("AWS access key ID", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
]


@dataclass(frozen=True)
class Finding:
    severity: str
    path: str
    line: int | None
    title: str
    advice: str


def scan(folder: str | Path) -> dict:
    root = Path(folder).resolve()
    if not root.is_dir():
        raise ValueError(f"Not a directory: {root}")
    findings = []
    stats = {"files": 0, "text_files": 0, "skipped_content": 0, "skipped_links": 0}

    def add(severity, path, title, advice, line=None):
        findings.append(Finding(severity, path, line, title, advice))

    def walk_error(error):
        add("warning", ".", "Directory could not be read", "Check folder permissions; the scan is incomplete.")

    for current, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not (Path(current) / d).is_symlink() and not os.path.islink(Path(current) / d))
        for name in sorted(files):
            file = Path(current) / name
            relative = file.relative_to(root).as_posix()
            if file.is_symlink():
                stats["skipped_links"] += 1
                continue
            stats["files"] += 1
            lower = name.lower()
            if (lower == ".env" or lower.startswith(".env.")) and not lower.endswith((".example", ".sample", ".template")):
                add("warning", relative, "Environment file", "Review locally; keep real credentials out of version control.")
            if lower in {"id_rsa", "id_ed25519", "credentials", ".npmrc", ".pypirc"} or lower.endswith((".p12", ".pfx")):
                add("warning", relative, "Potentially sensitive file", "Check this file before sharing; it may contain credentials.")
            try:
                size = file.stat().st_size
                if size > 50 * 1024 * 1024:
                    add("warning", relative, "Large file (>50 MiB)", "Consider Git LFS or a separate download.")
                if size > TEXT_LIMIT:
                    stats["skipped_content"] += 1
                    continue
                data = file.read_bytes()
                if b"\x00" in data:
                    stats["skipped_content"] += 1
                    continue
                try:
                    content = data.decode("utf-8-sig")
                except UnicodeDecodeError:
                    stats["skipped_content"] += 1
                    continue
                stats["text_files"] += 1
                for number, line in enumerate(content.splitlines(), 1):
                    for title, pattern in RULES:
                        if pattern.search(line):
                            add("error", relative, title, "If real, revoke or rotate the credential and remove it from files and Git history.", number)
            except OSError:
                add("warning", relative, "File could not be read", "Check permissions; this file was not inspected.")
    names = {p.name.lower() for p in root.iterdir()}
    for present, title, advice in [
        (any(n.startswith("readme") for n in names), "Missing README", "Explain what the project does and how to run it."),
        (any(n.startswith(("license", "licence")) for n in names), "Missing license", "Choose a license so others know how they may use your project."),
        (".gitignore" in names, "Missing .gitignore", "Add ignore rules for generated files and local credentials."),
    ]:
        if not present:
            add("info", ".", title, advice)
    findings.sort(key=lambda f: ({"error": 0, "warning": 1, "info": 2}[f.severity], f.path, f.line or 0))
    return {"root": str(root), "stats": stats, "findings": [asdict(f) for f in findings]}
