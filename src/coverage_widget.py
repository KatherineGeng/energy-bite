"""Nutrition coverage badge — isolated HTML; tooltip expands iframe on hover/click."""

from __future__ import annotations

import html

import streamlit.components.v1 as components

from src.nutrition import (
    covered_categories,
    coverage_detail_rows,
    coverage_summary,
)

ACCENT = "#8DA399"
_BASE_H = 30
_EXPANDED_H = 240


def _tip_table_html(menu_row: dict) -> str:
    rows = coverage_detail_rows(menu_row)
    body = "".join(
        f"<tr><td>{html.escape(r['营养类别'])}</td>"
        f"<td class='mark'>{html.escape(r['覆盖'])}</td></tr>"
        for r in rows
    )
    hit = covered_categories(menu_row)
    foot = html.escape("已覆盖：" + "、".join(hit)) if hit else "尚未分析或未匹配营养类"
    return (
        f"<table><thead><tr><th>类别</th><th>覆盖</th></tr></thead>"
        f"<tbody>{body}</tbody></table>"
        f"<span class='foot'>{foot}</span>"
        f"<span class='hint'>移开光标关闭 · 点击 i 可固定/关闭</span>"
    )


def _frame_resize_script(base_h: int, expanded_h: int) -> str:
    return f"""
<script>
(function() {{
  function setH(h) {{
    window.parent.postMessage({{type: 'streamlit:setFrameHeight', height: h}}, '*');
  }}
  const icon = document.querySelector('.cov-i');
  const tip = document.querySelector('.cov-tip');
  if (!icon || !tip) return;
  const base = {base_h};
  const expanded = {expanded_h};
  let pinned = false;
  const open = () => {{ tip.classList.add('open'); setH(expanded); }};
  const close = () => {{ if (!pinned) {{ tip.classList.remove('open'); setH(base); }} }};
  icon.addEventListener('mouseenter', open);
  icon.addEventListener('focus', open);
  tip.addEventListener('mouseenter', open);
  icon.addEventListener('mouseleave', (e) => {{
    if (!tip.contains(e.relatedTarget)) close();
  }});
  tip.addEventListener('mouseleave', (e) => {{
    if (!icon.contains(e.relatedTarget) && !pinned) close();
  }});
  icon.addEventListener('click', (e) => {{
    e.preventDefault();
    pinned = !pinned;
    if (pinned) open();
    else {{ tip.classList.remove('open'); setH(base); }}
  }});
  setH(base);
}})();
</script>
"""


def _coverage_styles() -> str:
    return f"""
* {{ box-sizing: border-box; }}
html, body {{
  margin: 0; padding: 0; background: transparent;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}}
.wrap {{
  display: inline-block;
  position: relative;
  font-size: 0.76rem;
  color: #64748B;
  vertical-align: baseline;
}}
.cov-i {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 0.9rem;
  height: 0.9rem;
  margin-left: 0.12rem;
  font-size: 0.58rem;
  font-weight: 700;
  font-style: italic;
  color: {ACCENT};
  border: 1px solid rgba(141, 163, 153, 0.55);
  border-radius: 50%;
  cursor: help;
  vertical-align: super;
  outline: none;
}}
.cov-tip {{
  display: none;
  position: absolute;
  z-index: 99999;
  right: 0;
  bottom: calc(100% + 6px);
  min-width: 11.5rem;
  max-width: 16rem;
  padding: 0.45rem 0.5rem;
  background: #fff;
  border: 1px solid rgba(141, 163, 153, 0.35);
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(30, 41, 59, 0.12);
  font-size: 0.72rem;
  color: #1E293B;
  text-align: left;
  white-space: normal;
}}
.cov-tip.open {{ display: block; }}
.cov-tip-title {{
  display: block;
  font-weight: 600;
  margin-bottom: 0.25rem;
  font-size: 0.72rem;
}}
table {{
  width: 100%;
  border-collapse: collapse;
  margin: 0.2rem 0;
  font-size: 0.7rem;
}}
th, td {{
  border-bottom: 1px solid rgba(141, 163, 153, 0.2);
  padding: 0.2rem 0.15rem;
}}
.mark {{ text-align: center; color: {ACCENT}; }}
.foot {{ display: block; color: #64748B; font-size: 0.66rem; margin-top: 0.15rem; }}
.hint {{ display: block; color: #94A3B8; font-size: 0.6rem; margin-top: 0.2rem; }}
"""


def _coverage_badge_document(menu_row: dict) -> str:
    summary = html.escape(coverage_summary(menu_row))
    tip = _tip_table_html(menu_row)
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>{_coverage_styles()}</style></head><body>
<span class="wrap">营养覆盖 {summary}
<span class="cov-i" tabindex="0" aria-label="查看营养覆盖">i</span>
<span class="cov-tip"><span class="cov-tip-title">七大营养类覆盖</span>{tip}</span>
</span>
{_frame_resize_script(_BASE_H, _EXPANDED_H)}
</body></html>"""


def render_coverage_badge(menu_row: dict, key: str, *, height: int = _BASE_H) -> None:
    """Inline coverage summary + i; table on hover/click of i."""
    components.html(_coverage_badge_document(menu_row), height=height, scrolling=False)


def _meal_headline_document(
    menu_name: str,
    meta_prefix: str,
    menu_row: dict,
    *,
    meal_type: str = "",
    ai_fresh: bool = False,
) -> str:
    summary = html.escape(coverage_summary(menu_row))
    tip = _tip_table_html(menu_row)
    name = html.escape(menu_name)
    prefix = html.escape(meta_prefix)
    fresh = ' <span class="ai-tag">AI新菜</span>' if ai_fresh else ""
    if meal_type:
        lead = f'<span class="label">{html.escape(meal_type)}</span> · <strong>{name}</strong>{fresh} ·'
    else:
        lead = f"· <strong>{name}</strong>{fresh} ·"
    headline_h = 38 if meal_type else 34
    expanded_h = headline_h + _EXPANDED_H - _BASE_H
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
{_coverage_styles()}
.head {{
  margin: 0;
  font-size: 0.92rem;
  line-height: 1.45;
  color: #1E293B;
}}
.label {{ color: {ACCENT}; font-weight: 600; }}
.meta {{ color: #64748B; font-size: 0.76rem; }}
.ai-tag {{
  display: inline-block;
  margin-left: 0.2rem;
  padding: 0 0.3rem;
  font-size: 0.62rem;
  font-weight: 600;
  color: #fff;
  background: {ACCENT};
  border-radius: 4px;
  vertical-align: middle;
}}
</style></head><body>
<p class="head">
  {lead}
  <span class="meta">{prefix}营养覆盖 {summary}<span class="wrap"><span class="cov-i" tabindex="0">i</span><span class="cov-tip"><span class="cov-tip-title">七大营养类覆盖</span>{tip}</span></span></span>
</p>
{_frame_resize_script(headline_h, expanded_h)}
</body></html>"""


def render_meal_headline(
    meal_type: str,
    row: dict,
    *,
    idx: int,
    locked: bool,
    widget_key: str,
    ai_fresh: bool = False,
) -> None:
    tags_str = str(row.get("energy_tags", "")).replace("·", " · ")
    if locked:
        meta_prefix = f"{tags_str} · "
    else:
        meta_prefix = f"{tags_str} · ⏱ {row['prep_minutes']} min · "

    headline_h = 38 if idx == 0 else 34
    if idx > 0:
        doc = _meal_headline_document(row["menu_name"], meta_prefix, row, ai_fresh=ai_fresh)
    else:
        doc = _meal_headline_document(
            row["menu_name"], meta_prefix, row, meal_type=meal_type, ai_fresh=ai_fresh
        )

    components.html(doc, height=headline_h, scrolling=False)
