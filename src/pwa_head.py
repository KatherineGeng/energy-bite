"""iOS / PWA head tags + parent-document icon/title override."""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

APP_DISPLAY_NAME = "简愈一人食"
# Bump when icon PNGs change so iOS/Safari refetch (static path is cached aggressively).
ICON_CACHE_BUST = "5039"


def inject_pwa_head() -> None:
    st.markdown(
        f"""
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="default">
        <meta name="apple-mobile-web-app-title" content="{APP_DISPLAY_NAME}">
        <meta name="application-name" content="{APP_DISPLAY_NAME}">
        <meta name="theme-color" content="#8DA399">
        <link rel="manifest" href="/app/static/manifest.webmanifest">
        """,
        unsafe_allow_html=True,
    )


def inject_ios_home_screen_fix() -> None:
    """Force parent <title>, apple-mobile-web-app-title, and PNG apple-touch-icon.

    iOS Safari does not accept SVG touch icons. Streamlit's SPA shell often ships
    default Streamlit branding before markdown runs — rewrite the parent document
    and keep watching for Streamlit re-injecting the red favicon.
    """
    components.html(
        f"""
        <script>
        (function () {{
          const NAME = {APP_DISPLAY_NAME!r};
          const VER = {ICON_CACHE_BUST!r};
          const doc = window.parent.document;
          const origin = window.parent.location.origin;
          const icon180 = origin + "/app/static/apple-touch-icon.png?v=" + VER;
          const icon512 = origin + "/app/static/icon-512.png?v=" + VER;
          const favicon = origin + "/app/static/favicon.png?v=" + VER;

          function upsertMeta(name, content) {{
            let el = doc.querySelector('meta[name="' + name + '"]');
            if (!el) {{
              el = doc.createElement("meta");
              el.setAttribute("name", name);
              doc.head.appendChild(el);
            }}
            el.setAttribute("content", content);
          }}

          function upsertLink(rel, href, sizes, type) {{
            let el = doc.querySelector('link[rel="' + rel + '"]' + (sizes ? '[sizes="' + sizes + '"]' : ""));
            if (!el) {{
              el = doc.createElement("link");
              el.setAttribute("rel", rel);
              if (sizes) el.setAttribute("sizes", sizes);
              if (type) el.setAttribute("type", type);
              doc.head.appendChild(el);
            }}
            el.setAttribute("href", href);
          }}

          function stripStreamlitIcons() {{
            doc.querySelectorAll('link[rel="icon"], link[rel="shortcut icon"], link[rel="apple-touch-icon"]').forEach(function (node) {{
              const href = (node.getAttribute("href") || "").toLowerCase();
              // Keep our static PNGs; drop Streamlit media / emoji / svg defaults.
              if (href.indexOf("/app/static/") === -1) {{
                node.parentNode && node.parentNode.removeChild(node);
              }}
            }});
          }}

          function apply() {{
            try {{
              doc.title = NAME;
              upsertMeta("apple-mobile-web-app-title", NAME);
              upsertMeta("application-name", NAME);
              upsertMeta("apple-mobile-web-app-capable", "yes");
              upsertMeta("mobile-web-app-capable", "yes");
              stripStreamlitIcons();
              upsertLink("apple-touch-icon", icon180, "180x180", "image/png");
              upsertLink("apple-touch-icon", icon512, "512x512", "image/png");
              upsertLink("icon", favicon, "32x32", "image/png");
              upsertLink("shortcut icon", favicon, null, "image/png");
              let man = doc.querySelector('link[rel="manifest"]');
              if (!man) {{
                man = doc.createElement("link");
                man.setAttribute("rel", "manifest");
                doc.head.appendChild(man);
              }}
              man.setAttribute("href", origin + "/app/static/manifest.webmanifest?v=" + VER);
            }} catch (e) {{}}
          }}

          apply();
          setTimeout(apply, 200);
          setTimeout(apply, 800);
          setTimeout(apply, 2000);

          try {{
            const obs = new MutationObserver(function () {{ apply(); }});
            obs.observe(doc.head, {{ childList: true, subtree: true }});
            obs.observe(doc.querySelector("title") || doc.head, {{ childList: true, characterData: true, subtree: true }});
          }} catch (e) {{}}
        }})();
        </script>
        """,
        height=0,
        width=0,
    )
