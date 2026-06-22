"""Inject PWA / iOS icons — same-origin static + head meta for Safari."""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

from src.constants import APP_VERSION

_ROOT = Path(__file__).resolve().parent.parent
_ICON = _ROOT / "static" / "apple-touch-icon.png"
if not _ICON.exists():
    _ICON = _ROOT / "apple-touch-icon.png"

_GITHUB_ICON = (
    f"https://raw.githubusercontent.com/KatherineGeng/energy-bite/main/static/apple-touch-icon.png?v={APP_VERSION}"
)


def inject_pwa_head() -> None:
    if not _ICON.exists():
        st.warning("图标文件缺失：static/apple-touch-icon.png")
        return

    icon_b64 = base64.b64encode(_ICON.read_bytes()).decode("ascii")
    data_uri = f"data:image/png;base64,{icon_b64}"

    snippet = f"""
    <script>
    (function () {{
        var github = "{_GITHUB_ICON}";
        var dataUri = "{data_uri}";

        function upsertLink(doc, rel, href, sizes) {{
            if (!doc || !doc.head) return;
            var el = doc.querySelector('link[rel="' + rel + '"]');
            if (!el) {{
                el = doc.createElement("link");
                el.rel = rel;
                doc.head.appendChild(el);
            }}
            el.href = href;
            el.type = "image/png";
            if (sizes) el.setAttribute("sizes", sizes);
        }}

        function upsertMeta(doc, name, content) {{
            if (!doc || !doc.head) return;
            var el = doc.querySelector('meta[name="' + name + '"]');
            if (!el) {{
                el = doc.createElement("meta");
                el.name = name;
                doc.head.appendChild(el);
            }}
            el.content = content;
        }}

        function upsertProperty(doc, property, content) {{
            if (!doc || !doc.head) return;
            var el = doc.querySelector('meta[property="' + property + '"]');
            if (!el) {{
                el = doc.createElement("meta");
                el.setAttribute("property", property);
                doc.head.appendChild(el);
            }}
            el.content = content;
        }}

        function applyIcons(doc, href) {{
            upsertLink(doc, "icon", href, "32x32");
            upsertLink(doc, "apple-touch-icon", href, "180x180");
            upsertLink(doc, "apple-touch-icon-precomposed", href, "180x180");
            upsertProperty(doc, "og:image", href);
            upsertMeta(doc, "twitter:image", href);
        }}

        function injectAll(href) {{
            applyIcons(document, href);
            upsertMeta(document, "apple-mobile-web-app-title", "简愈");
            upsertMeta(document, "theme-color", "#8DA399");
            try {{
                applyIcons(window.parent.document, href);
                upsertMeta(window.parent.document, "apple-mobile-web-app-title", "简愈");
                upsertMeta(window.parent.document, "theme-color", "#8DA399");
            }} catch (e) {{}}
        }}

        var loc = window.parent && window.parent.location ? window.parent.location : window.location;
        var sameOrigin = loc.origin + "/apple-touch-icon.png?v={APP_VERSION}";

        injectAll(sameOrigin);

        var test = new Image();
        test.onload = function () {{ injectAll(sameOrigin); }};
        test.onerror = function () {{
            var test2 = new Image();
            test2.onload = function () {{ injectAll(github); }};
            test2.onerror = function () {{ injectAll(dataUri); }};
            test2.src = github;
        }};
        test.src = sameOrigin;
    }})();
    </script>
    """

    wrapped = f'<div style="display:none;height:0;overflow:hidden;">{snippet}</div>'
    if hasattr(st, "html"):
        st.html(wrapped)
    else:
        import streamlit.components.v1 as components

        components.html(wrapped, height=0, width=0)
