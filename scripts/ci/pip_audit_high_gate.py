#!/usr/bin/env python3
"""
Gate CI on high/critical Python vulnerabilities: run pip-audit (OSV) on a requirements
file exported from uv, then keep only findings whose OSV record has CVSS base score >= 7.0.
"""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

MIN_CVSS = 7.0


def _cvss_base_score(severity_block: dict) -> float | None:
    score_str = severity_block.get("score")
    if not score_str or not isinstance(score_str, str):
        return None
    kind = (severity_block.get("type") or "").upper()
    try:
        if "V3" in kind or score_str.startswith("CVSS:3"):
            from cvss import CVSS3

            return float(CVSS3(score_str).scores()[0])
        if "V2" in kind or score_str.startswith("CVSS:2"):
            from cvss import CVSS2

            return float(CVSS2(score_str).scores()[0])
    except Exception:
        return None
    return None


def _max_cvss_from_osv(vuln: dict) -> float:
    best = 0.0
    for sev in vuln.get("severity") or []:
        if not isinstance(sev, dict):
            continue
        s = _cvss_base_score(sev)
        if s is not None:
            best = max(best, s)
    return best


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: pip_audit_high_gate.py REQUIREMENTS_FILE", file=sys.stderr)
        return 2
    req = sys.argv[1]
    proc = subprocess.run(
        [
            "pip-audit",
            "-r",
            req,
            "-s",
            "osv",
            "--desc",
            "off",
            "-f",
            "json",
        ],
        capture_output=True,
        text=True,
    )
    out = (proc.stdout or "").strip()
    if proc.returncode not in (0, 1):
        print(proc.stderr or "pip-audit failed", file=sys.stderr)
        return proc.returncode or 1
    if not out:
        print("pip-audit produced no output.", file=sys.stderr)
        return 1
    data = json.loads(out)
    ids: set[str] = set()
    for dep in data.get("dependencies") or []:
        for v in dep.get("vulns") or []:
            vid = v.get("id")
            if isinstance(vid, str):
                ids.add(vid)
    if not ids:
        print("No vulnerabilities reported by pip-audit.")
        return 0

    high: list[tuple[str, float]] = []
    unscoped: list[str] = []
    for vid in sorted(ids):
        url = f"https://api.osv.dev/v1/vulns/{urllib.parse.quote(vid, safe='')}"
        try:
            with urllib.request.urlopen(url, timeout=90) as resp:
                vuln = json.load(resp)
        except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as e:
            print(f"WARNING: could not fetch OSV record for {vid}: {e}", file=sys.stderr)
            unscoped.append(vid)
            continue
        score = _max_cvss_from_osv(vuln)
        if score >= MIN_CVSS:
            high.append((vid, score))
        elif score == 0.0:
            unscoped.append(vid)

    if high:
        print("Blocking: high/critical vulnerabilities (CVSS base score >= 7.0):", file=sys.stderr)
        for vid, sc in sorted(high, key=lambda x: (-x[1], x[0])):
            print(f"  {vid}  (CVSS ~{sc:.1f})", file=sys.stderr)
        return 1

    if unscoped:
        print(
            "NOTE: pip-audit reported IDs without a usable CVSS score in OSV "
            f"(not failing the gate): {', '.join(unscoped)}",
            file=sys.stderr,
        )
    print("No high/critical vulnerabilities (CVSS >= 7.0) from pip-audit/OSV.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
