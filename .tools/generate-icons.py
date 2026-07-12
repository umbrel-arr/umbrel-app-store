#!/usr/bin/env python3

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / ".assets" / "icon-sources"
OUTPUT = ROOT / ".assets" / "icons"

OFFICIAL_ICONS = (
    "bazarr",
    "flaresolverr",
    "lidarr",
    "overseerr",
    "prowlarr",
    "qbittorrent",
    "radarr",
    "sabnzbd",
    "sonarr",
)


def read_source(name):
    return (SOURCES / f"{name}.svg").read_text(encoding="utf-8").strip() + "\n"


def add_4k_badge(svg, fill, text_fill):
    badge = f"""
  <g aria-label="4K edition">
    <rect x="164" y="174" width="76" height="50" rx="13" fill="{fill}" stroke="#FFFFFF" stroke-width="4"/>
    <text x="202" y="207" fill="{text_fill}" font-family="Inter, Arial, sans-serif" font-size="27" font-weight="800" text-anchor="middle">4K</text>
  </g>
"""
    return re.sub(r"</svg>\s*$", badge + "</svg>\n", svg)


def wrap_mark(svg, background, inset):
    opening = re.match(r"\s*<svg\b([^>]*)>", svg)
    if not opening:
        raise ValueError("icon source has no SVG root")
    attributes = opening.group(1)
    view_box = re.search(r'viewBox="([^"]+)"', attributes)
    if not view_box:
        raise ValueError("icon source has no viewBox")
    body = re.sub(r"\s*</svg>\s*$", "", svg[opening.end() :])
    size = 256 - (inset * 2)
    return f"""<svg width="256" height="256" viewBox="0 0 256 256" fill="none" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
  <rect width="256" height="256" fill="{background}"/>
  <svg x="{inset}" y="{inset}" width="{size}" height="{size}" viewBox="{view_box.group(1)}" preserveAspectRatio="xMidYMid meet">
{body}
  </svg>
</svg>
"""


def umbrelarr_icon():
    return """<svg width="256" height="256" viewBox="0 0 256 256" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="256" height="256" fill="#102A43"/>
  <path d="M0 0H256V78H0Z" fill="#153A59"/>
  <path d="M48 82H105L124 104H208V181H48V82Z" fill="#19C3C8"/>
  <path d="M48 82H105L124 104H208V181H48V82Z" stroke="#E8FCFF" stroke-width="11" stroke-linejoin="round"/>
  <circle cx="86" cy="143" r="14" fill="#FFCF5C"/>
  <circle cx="170" cy="143" r="14" fill="#FF7A66"/>
  <path d="M105 143H151" stroke="#E8FCFF" stroke-width="11" stroke-linecap="round"/>
  <path d="M128 48V91" stroke="#E8FCFF" stroke-width="11" stroke-linecap="round"/>
</svg>
"""


def expected_icons():
    icons = {name: read_source(name) for name in OFFICIAL_ICONS}
    icons["radarr-4k"] = add_4k_badge(icons["radarr"], "#171C24", "#FFD052")
    icons["sonarr-4k"] = add_4k_badge(icons["sonarr"], "#00CCFF", "#17202B")
    icons["privado-vpn"] = wrap_mark(read_source("privado-vpn"), "#1C1E22", 18)
    icons["profilarr"] = wrap_mark(read_source("profilarr"), "#EAF2FF", 42)
    icons["umbrelarr"] = umbrelarr_icon()
    return icons


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    stale = []
    for name, content in expected_icons().items():
        path = OUTPUT / f"{name}.svg"
        encoded = content.encode()
        if args.check:
            if not path.exists() or path.read_bytes() != encoded:
                stale.append(path.relative_to(ROOT))
        else:
            path.write_bytes(encoded)

    if stale:
        print("Generated icons are stale:")
        for path in stale:
            print(f"  {path}")
        raise SystemExit(1)
    if not args.check:
        print(f"Generated {len(expected_icons())} app icons.")


if __name__ == "__main__":
    main()
