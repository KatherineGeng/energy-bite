"""Inject PWA / iOS icons — three strategies for Streamlit Cloud + iOS Safari."""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

from src.constants import APP_VERSION

_ROOT = Path(__file__).resolve().parent.parent
_ICON = _ROOT / "apple-touch-icon.png"
if not _ICON.exists():
    _ICON = _ROOT / "assets" / "apple-touch-icon.png"

# Strategy B: public CDN URL (iOS 最可靠，需已 push 到 GitHub main)
_ICON_URL = f"https://raw.githubusercontent.com/KatherineGeng/energy-bite/main/apple-touch-icon.png?v={APP_VERSION}"


def inject_pwa_head() -> None:
    """A: page_icon in set_page_config  B: GitHub PNG in <head>  C: data-URI fallback."""
    if not _ICON.exists():
        st.warning("图标文件缺失：apple-touch-icon.png")
        return

    icon_b64 = base64.b64encode(_ICON.read_bytes()).decode("ascii")
    data_uri = f"data:image/png;base64,{icon_b64}"

    snippet = f"""
        <script>
        (function () {{
            try {{
                const doc = window.parent.document;
                const github = "{_ICON_URL}";
                const dataUri = "{data_uri}";

                function setLink(rel, href, sizes) {{
                    var sel = 'link[rel="' + rel + '"]';
                    var el = doc.querySelector(sel);
                    if (!el) {{
                        el = doc.createElement("link");
                        el.rel = rel;
                        doc.head.appendChild(el);
                    }}
                    el.href = href;
                    el.type = "image/png";
                    if (sizes) el.setAttribute("sizes", sizes);
                }}

                setLink("apple-touch-icon", github, "180x180");
                setLink("apple-touch-icon-precomposed", github, "180x180");
                setLink("icon", github, "180x180");

                var probe = new Image();
                probe.onerror = function () {{
                    setLink("apple-touch-icon", dataUri, "180x180");
                    setLink("icon", dataUri, "32x32");
                }};
                probe.src = github;

                var metaTitle = doc.querySelector('meta[name="apple-mobile-web-app-title"]');
                if (!metaTitle) {{
                    metaTitle = doc.createElement("meta");
                    metaTitle.name = "apple-mobile-web-app-title";
                    doc.head.appendChild(metaTitle);
                }}
                metaTitle.content = "简愈";

                var theme = doc.querySelector('meta[name="theme-color"]');
                if (!theme) {{
                    theme = doc.createElement("meta");
                    theme.name = "theme-color";
                    doc.head.appendChild(theme);
                }}
                theme.content = "#8DA399";
            }} catch (e) {{
                console.warn("PWA icon inject failed", e);
            }}
        }})();
        </script>
        """

    wrapped = f'<div style="display:none;height:0;overflow:hidden;margin:0;padding:0;">{snippet}</div>'

    if hasattr(st, "html"):
        st.html(wrapped)
    else:
        import streamlit.components.v1 as components

        components.html(wrapped, height=0, width=0)
