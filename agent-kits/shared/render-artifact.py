#!/usr/bin/env python3
'''Render provider artifacts with script-safe JSON configuration, never raw substitution.'''
import argparse
import json
from pathlib import Path
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001

ROOT=Path(__file__).resolve().parents[2]
TEMPLATES={
    "jira-picker": ("jira-sync/assets/jira-picker.template.html", ("SERVER_PROJECTS","SERVER_SEARCH","CLOUD_ID")),
    "jira-live": ("roadmap-dashboard/assets/jira-live.template.html", ("SERVER_SEARCH","CLOUD_ID","LABEL","TITULO")),
    "confluence-tree": ("confluence-publish/assets/tree-browser.template.html", ("SERVER","CLOUD_ID","HOME_ID","SPACE_KEY","SPACE_NAME","SPACE_INITIALS","DEFAULT_NAME")),
}
MAX_CONFIG=65536

def render(kind, config):
    if kind not in TEMPLATES:
        raise ValueError("unknown template")
    path, fields=TEMPLATES[kind]
    if type(config) is not dict or set(config)!=set(fields):
        raise ValueError("configuration fields do not match template")
    if any(type(value) is not str or len(value)>16384 for value in config.values()):
        raise ValueError("configuration values must be bounded strings")
    encoded=json.dumps(config,ensure_ascii=True,separators=(",",":"))
    if len(encoded.encode("ascii"))>MAX_CONFIG:
        raise ValueError("configuration exceeds budget")
    encoded=encoded.replace("<","\\u003c").replace(">","\\u003e").replace("&","\\u0026")
    with (ROOT/"skills"/path).open("rb") as handle:
        raw=handle.read(1024*1024+1)
    if len(raw)>1024*1024:
        raise ValueError("template exceeds budget")
    template=raw.decode("utf-8")
    if template.count("{{CONFIG_JSON}}")!=1:
        raise ValueError("template configuration slot missing or duplicated")
    if "{{" in template.replace("{{CONFIG_JSON}}",""):
        raise ValueError("unresolved template slot")
    return template.replace("{{CONFIG_JSON}}",encoded)

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template",choices=sorted(TEMPLATES),required=True)
    parser.add_argument("--config",required=True,help="JSON file, or - for stdin; rendered HTML goes to stdout")
    args=parser.parse_args(argv)
    try:
        if args.config=="-":
            raw=sys.stdin.buffer.read(MAX_CONFIG+1)
        else:
            with open(args.config,"rb") as handle:
                raw=handle.read(MAX_CONFIG+1)
        if len(raw)>MAX_CONFIG:
            raise ValueError("configuration exceeds budget")
        data=json.loads(raw.decode("utf-8"))
        print(render(args.template,data),end="")
    except (ValueError,OSError,UnicodeError,RecursionError):
        print("render-artifact: invalid or unavailable configuration/template",file=sys.stderr)
        return 2
    return 0

if __name__=="__main__":
    raise SystemExit(main())
