"""Inject PWA / iOS icons into the parent document <head> (Streamlit workaround)."""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit.components.v1 as components

_ROOT = Path(__file__).resolve().parent.parent
_ICON = _ROOT / "apple-touch-icon.png"
if not _ICON.exists():
    _ICON = _ROOT / "assets" / "apple-touch-icon.png"

# Public fallback if data-URI is blocked by iOS in some contexts.
_ICON_URL = "https://raw.githubusercontent.com/KatherineGeng/energy-bite/main/apple-touch-icon.png"


def inject_pwa_head() -> None:
    if not _ICON.exists():
        return

    icon_b64 = base64.b64encode(_ICON.read_bytes()).decode("ascii")
    data_uri = f"data:image/png;base64,{icon_b64}"

    components.html(
        f"""
        <script>
        (function () {{
            const doc = window.parent.document;
            const href = "{data_uri}";
            const fallback = "{_ICON_URL}";

            function upsertLink(rel, sizes) {{
                let nodes = doc.querySelectorAll('link[rel="' + rel + '"]');
                let el = nodes.length ? nodes[0] : doc.createElement("link");
                el.rel = rel;
                el.href = href;
                el.type = "image/png";
                if (sizes) el.setAttribute("sizes", sizes);
                if (!nodes.length) doc.head.appendChild(el);
            }}

            upsertLink("icon", "32x32");
            upsertLink("apple-touch-icon", "180x180");
            upsertLink("apple-touch-icon-precomposed", "180x180");

            let meta = doc.querySelector('meta[name="apple-mobile-web-app-title"]');
            if (!meta) {{
                meta = doc.createElement("meta");
                meta.name = "apple-mobile-web-app-title";
                doc.head.appendChild(meta);
            }}
            meta.content = "简愈一人食";

            let theme = doc.querySelector('meta[name="theme-color"]');
            if (!theme) {{
                theme = doc.createElement("meta");
                theme.name = "theme-color";
                doc.head.appendChild(theme);
            }}
            theme.content = "#8DA399";

            // Fallback: swap to GitHub-hosted PNG if data URI fails on device.
            const probe = new Image();
            probe.onerror = function () {{
                doc.querySelectorAll('link[rel="icon"], link[rel="apple-touch-icon"], link[rel="apple-touch-icon-precomposed"]')
                    .forEach(function (node) {{ node.href = fallback; }});
            }};
            probe.src = href;
        }})();
        </script>
        """,
        height=0,
        width=0,
    )
