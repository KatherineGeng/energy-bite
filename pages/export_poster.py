"""Sharing — poster maker, import, and share trail."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import streamlit as st

from src.database import (
    append_menu_from_share,
    get_menu_by_id,
    init_database,
    record_menu_archive,
)
from src.export import generate_poster
from src.image_library import apply_gallery_pick_action, render_gallery_picker, save_uploads_to_library
from src.session_hydrate import hydrate_today_state, menu_ids_for_date
from src.share_code import ShareCodeError, decode_share_code, encode_day_menu_share_text

_SAMPLE_POSTER = Path(__file__).resolve().parent.parent / "assets" / "sample_poster.png"


def _inject_export_ui_css() -> None:
    st.markdown(
        """
        <style>
        .eb-poster-default-hint {
            font-size: 0.85rem !important;
            color: #64748B;
            text-align: center;
            white-space: nowrap;
            margin: 0 0 0.45rem;
            line-height: 1.35;
        }
        .eb-export-panel {
            margin: 0.65rem 0 0.15rem;
            padding: 0.85rem 0.65rem 0.35rem;
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.55);
            border: 1px solid rgba(141, 163, 153, 0.18);
        }
        div[data-testid="stHorizontalBlock"] button {
            min-height: 2.85rem !important;
            font-weight: 600 !important;
            font-size: 0.82rem !important;
        }
        .eb-poster-hero {
            margin: 0 0 0.75rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _today_menu_ids() -> list[str]:
    today = st.session_state.get("today_date", date.today().isoformat())
    ids = menu_ids_for_date(today)
    if ids:
        return ids
    return list(st.session_state.get("final_daily_list") or st.session_state.get("current_day_menus") or [])


def _menu_rows_for_ids(menu_ids: list[str]) -> list[dict]:
    rows: list[dict] = []
    for mid in menu_ids:
        row = get_menu_by_id(mid)
        if row:
            rows.append(row)
    return rows


def _render_menu_summary(date_str: str, menu_ids: list[str]) -> None:
    if not menu_ids:
        st.info(f"{date_str} 暂无已保存的菜单记录。")
        return
    for mid in menu_ids:
        row = get_menu_by_id(mid)
        if not row:
            continue
        st.markdown(f"**{row.get('meal_type', '')} · {row['menu_name']}**")
        st.caption(str(row.get("energy_tags", "")).replace("·", " · "))


def _append_poster_history(date_str: str, menu_ids: list[str], share_text: str = "") -> None:
    history: list[dict] = list(st.session_state.get("poster_history") or [])
    entry = {
        "date": date_str,
        "menu_ids": list(menu_ids),
        "share_text": share_text,
        "saved_at": date.today().isoformat(),
    }
    history = [h for h in history if h.get("date") != date_str]
    history.insert(0, entry)
    st.session_state.poster_history = history[:20]


def _record_shared_menus(day: str, menu_ids: list[str]) -> None:
    if menu_ids:
        record_menu_archive(day, menu_ids, is_shared=True)


def _render_default_poster() -> None:
    st.markdown('<div class="eb-poster-hero">', unsafe_allow_html=True)
    if st.session_state.get("poster_bytes"):
        st.image(st.session_state.poster_bytes, caption="最新生活志海报", use_container_width=True)
    elif _SAMPLE_POSTER.is_file():
        st.image(str(_SAMPLE_POSTER), caption="样本海报 · 生成后将在此展示", use_container_width=True)
    else:
        st.caption("生成海报后将在此预览")
    st.markdown("</div>", unsafe_allow_html=True)


def _render_poster_panel() -> None:
    today = date.today()
    today_iso = today.isoformat()
    default_ids = _today_menu_ids()

    if default_ids:
        st.markdown(
            '<p class="eb-poster-default-hint">默认使用「今日菜单」中当前/已确认的就餐计划。</p>',
            unsafe_allow_html=True,
        )
    else:
        st.info("请先在「菜单」页确认今日就餐计划。")

    selected_date = st.date_input("海报日期", value=today, key="export_poster_date")
    date_str = selected_date.isoformat()
    if date_str == today_iso and default_ids:
        menu_ids = default_ids
    else:
        menu_ids = menu_ids_for_date(date_str)

    if menu_ids:
        _render_menu_summary(date_str, menu_ids)

    uploaded = st.file_uploader(
        "上传实拍餐食（支持1-2张）",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="meal_photos",
    )
    if not uploaded:
        st.caption("未上传时可点「查看」打开 App 图片库，或使用默认生活方式图")
    if uploaded and len(uploaded) > 2:
        st.warning("最多上传 2 张照片，已自动使用前 2 张。")
        uploaded = uploaded[:2]

    gallery_photos = render_gallery_picker("poster_gallery", max_select=2)

    if st.button("生成海报", type="primary", use_container_width=True, key="gen_poster", disabled=not menu_ids):
        photos: list[bytes] = []
        if uploaded:
            save_uploads_to_library(uploaded, source="user")
            photos.extend(f.getvalue() for f in uploaded[:2])
        for data in gallery_photos:
            if len(photos) >= 2:
                break
            photos.append(data)
        photos = photos[:2]
        png_bytes = generate_poster(date_str=date_str, menu_ids=menu_ids, photos=photos)
        st.session_state.poster_bytes = png_bytes
        st.session_state.poster_filename = f"jianyu_{date_str}.png"
        st.session_state.poster_menu_ids = menu_ids
        st.session_state.poster_date_str = date_str
        st.session_state.poster_share_text = ""
        _append_poster_history(date_str, menu_ids)
        st.rerun()

    if st.session_state.get("poster_bytes"):
        dl_col, code_col = st.columns(2)
        with dl_col:
            st.download_button(
                "保存至本地",
                data=st.session_state.poster_bytes,
                file_name=st.session_state.get("poster_filename", "jianyu_poster.png"),
                mime="image/png",
                use_container_width=True,
                key="download_poster",
            )
        with code_col:
            if st.button("复制菜单口令", use_container_width=True, key="gen_poster_share_code"):
                ids = list(st.session_state.get("poster_menu_ids") or [])
                date_for_code = str(st.session_state.get("poster_date_str", date_str))
                rows = _menu_rows_for_ids(ids)
                if rows:
                    share_text = encode_day_menu_share_text(date_for_code, rows)
                    st.session_state.poster_share_text = share_text
                    _record_shared_menus(date_for_code, ids)
                    _append_poster_history(date_for_code, ids, share_text)
                else:
                    st.session_state.poster_share_text = ""

        share_text = st.session_state.get("poster_share_text", "")
        if share_text:
            st.text_area(
                "菜单口令（长按全选复制，发送给好友）",
                value=share_text,
                height=140,
                key="poster_share_code_display",
            )


def _render_import_panel() -> None:
    st.caption("粘贴朋友分享的简愈口令，一键存入私人菜单库。")
    pasted = st.text_area(
        "粘贴分享口令",
        placeholder="￥MENU:ING_001|ING_002:快速供能·肠脑舒缓:0.85￥",
        height=88,
        key="import_share_code",
    )
    import_name = st.text_input("自定义菜单名称（可选）", placeholder="留空则自动生成", key="import_menu_name")

    if st.button("确认导入", type="primary", use_container_width=True, key="import_menu"):
        try:
            payload = decode_share_code(pasted)
            new_id = append_menu_from_share(
                ingredient_ids=payload.ingredient_ids,
                energy_tags=payload.energy_tags,
                menu_name=import_name.strip(),
                description=f"由极客口令导入 · 预估分数 {payload.estimated_score:.2f}",
            )
            menu_row = get_menu_by_id(new_id)
            st.success(f"已导入 · {menu_row['menu_name']}（{new_id}）")
        except ShareCodeError as exc:
            st.error(str(exc))
        except ValueError as exc:
            st.error(str(exc))


def _render_trail_panel() -> None:
    history: list[dict] = list(st.session_state.get("poster_history") or [])
    if not history:
        st.caption("暂无海报分享记录。生成海报并复制口令后会在此保留。")
        return

    for idx, item in enumerate(history):
        date_str = str(item.get("date", ""))
        with st.container(border=True):
            st.markdown(f"**{date_str}**")
            ids = list(item.get("menu_ids") or [])
            if ids:
                _render_menu_summary(date_str, ids)
            share_text = str(item.get("share_text") or "")
            if share_text:
                st.text_area(
                    "分享口令",
                    value=share_text,
                    height=100,
                    key=f"trail_share_{idx}_{date_str}",
                )
            elif st.button("生成口令", key=f"trail_gen_{idx}_{date_str}", use_container_width=True):
                rows = _menu_rows_for_ids(ids)
                if rows:
                    code = encode_day_menu_share_text(date_str, rows)
                    item["share_text"] = code
                    history[idx] = item
                    st.session_state.poster_history = history
                    _record_shared_menus(date_str, ids)
                    st.rerun()


def _render_action_zone() -> None:
    if "export_action_panel" not in st.session_state:
        st.session_state.export_action_panel = None

    panel = st.session_state.export_action_panel
    col_a, col_b, col_c = st.columns(3, gap="small")
    with col_a:
        if st.button(
            "🖼️ 制作菜单海报",
            key="export_btn_poster",
            use_container_width=True,
            type="primary" if panel == "poster" else "secondary",
        ):
            st.session_state.export_action_panel = None if panel == "poster" else "poster"
            st.rerun()
    with col_b:
        if st.button(
            "📥 导入菜单口令",
            key="export_btn_import",
            use_container_width=True,
            type="primary" if panel == "import" else "secondary",
        ):
            st.session_state.export_action_panel = None if panel == "import" else "import"
            st.rerun()
    with col_c:
        if st.button(
            "📤 海报分享轨迹",
            key="export_btn_trail",
            use_container_width=True,
            type="primary" if panel == "trail" else "secondary",
        ):
            st.session_state.export_action_panel = None if panel == "trail" else "trail"
            st.rerun()

    if panel == "poster":
        st.markdown('<div class="eb-export-panel">', unsafe_allow_html=True)
        _render_poster_panel()
        st.markdown("</div>", unsafe_allow_html=True)
    elif panel == "import":
        st.markdown('<div class="eb-export-panel">', unsafe_allow_html=True)
        _render_import_panel()
        st.markdown("</div>", unsafe_allow_html=True)
    elif panel == "trail":
        st.markdown('<div class="eb-export-panel">', unsafe_allow_html=True)
        _render_trail_panel()
        st.markdown("</div>", unsafe_allow_html=True)


def render() -> None:
    init_database()
    hydrate_today_state()
    apply_gallery_pick_action()

    _inject_export_ui_css()

    if st.session_state.pop("review_complete", False):
        st.session_state.export_action_panel = "poster"
        st.success("回顾已完成 · 上传实拍，生成今日全日生活志海报吧。")

    if "poster_history" not in st.session_state:
        st.session_state.poster_history = []

    _render_default_poster()
    _render_action_zone()
