"""Inject PWA / iOS icons — Streamlit static path + CDN + data-URI."""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

from src.constants import APP_VERSION

_ROOT = Path(__file__).resolve().parent.parent
_ICON = _ROOT / "static" / "apple-touch-icon.png"
if not _ICON.exists():
    _ICON = _ROOT / "apple-touch-icon.png"

# Streamlit static URL (requires enableStaticServing = true in config.toml)
_STATIC_PATH = "/app/static/apple-touch-icon.png"
_CDN_URL = f"https://cdn.jsdelivr.net/gh/KatherineGeng/energy-bite@main/static/apple-touch-icon.png?v={APP_VERSION}"


def inject_pwa_head() -> None:
    if not _ICON.exists():
        st.warning("图标文件缺失：static/apple-touch-icon.png")
        return

    icon_b64 = base64.b64encode(_ICON.read_bytes()).decode("ascii")
    data_uri = f"data:image/png;base64,{icon_b64}"

    snippet = f"""
    <script>
    (function () {{
        var staticPath = "{_STATIC_PATH}";
        var cdn = "{_CDN_URL}";
        var dataUri = "{data_uri}";

        function upsertLink(doc, rel, href, sizes) {{
            if (!doc || !doc.head) return;
            var nodes = doc.querySelectorAll('link[rel="' + rel + '"]');
            var el = nodes.length ? nodes[0] : doc.createElement("link");
            el.rel = rel;
            el.href = href;
            el.type = "image/png";
            if (sizes) el.setAttribute("sizes", sizes);
            if (!nodes.length) doc.head.appendChild(el);
        }}

        function upsertMeta(doc, name, content) {{
            if (!doc || !doc.head) return;
            var el = doc.querySelector('meta[name="' + name + '"]');
            if (!el) {{ el = doc.createElement("meta"); el.name = name; doc.head.appendChild(el); }}
            el.content = content;
        }}

        function upsertProp(doc, property, content) {{
            if (!doc || !doc.head) return;
            var el = doc.querySelector('meta[property="' + property + '"]');
            if (!el) {{ el = doc.createElement("meta"); el.setAttribute("property", property); doc.head.appendChild(el); }}
            el.content = content;
        }}

        function apply(doc, href) {{
            upsertLink(doc, "icon", href, "32x32");
            upsertLink(doc, "apple-touch-icon", href, "180x180");
            upsertLink(doc, "apple-touch-icon-precomposed", href, "180x180");
            upsertLink(doc, "manifest", "/app/static/manifest.webmanifest");
            upsertProp(doc, "og:image", href);
            upsertMeta(doc, "twitter:image", href);
            upsertMeta(doc, "apple-mobile-web-app-title", "简愈");
            upsertMeta(doc, "theme-color", "#8DA399");
        }}

        function inject(href) {{
            apply(document, href);
            try {{ apply(window.parent.document, href); }} catch (e) {{}}
        }}

        function tryUrl(url, next) {{
            var img = new Image();
            img.onload = function () {{ inject(url); }};
            img.onerror = function () {{ if (next) next(); }};
            img.src = url;
        }}

        var loc = window.parent && window.parent.location ? window.parent.location : window.location;
        var sameOrigin = loc.origin + staticPath + "?v={APP_VERSION}";

        tryUrl(sameOrigin, function () {{
            tryUrl(cdn, function () {{ inject(dataUri); }});
        }});
    }})();
    </script>
    """

    wrapped = f'<div style="display:none;height:0;overflow:hidden;">{snippet}</div>'
    if hasattr(st, "html"):
        st.html(wrapped)
    else:
        import streamlit.components.v1 as components

        components.html(wrapped, height=0, width=0)
