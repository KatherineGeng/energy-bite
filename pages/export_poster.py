"""Sharing — poster maker, import, and share trail."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import streamlit as st

from src.database import (
    append_menu_from_share,
    get_menu_row,
    load_daily_meal_plan,
    record_menu_archive,
)
from src.export import generate_poster
from src.image_library import apply_gallery_pick_action, render_gallery_picker, save_uploads_to_library
from src.poster_store import (
    meals_for_poster,
    primary_menu_ids_for_poster,
    restore_poster_for_display,
    save_poster_state,
    user_has_generated_poster,
)
from src.session_hydrate import menu_ids_for_date
from src.share_code import ShareCodeError, decode_share_code, encode_day_menu_share_text

_SAMPLE_POSTER = Path(__file__).resolve().parent.parent / "assets" / "sample_poster.png"


def _show_poster_image(src) -> None:
    """Streamlit <1.38 lacks use_container_width on st.image (TypeError)."""
    try:
        st.image(src, use_container_width=True)
    except TypeError:
        st.image(src, width=720)


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
        .eb-export-top-actions [data-testid="stHorizontalBlock"] {
            flex-wrap: nowrap !important;
        }
        .eb-export-top-actions [data-testid="column"] {
            flex: 1 1 50% !important;
            min-width: 0 !important;
        }
        .eb-export-top-actions button {
            min-height: 2.55rem !important;
            font-weight: 600 !important;
            font-size: 0.84rem !important;
            padding: 0.35rem 0.2rem !important;
        }
        .eb-export-trail-action button {
            min-height: 2.55rem !important;
            font-weight: 600 !important;
            font-size: 0.84rem !important;
        }
        .eb-poster-hero {
            margin: 0.15rem 0 0.55rem;
        }
        .eb-poster-hero [data-testid="stImage"] {
            margin: 0 !important;
        }
        .eb-poster-hero [data-testid="stImage"] img {
            max-height: 46vh !important;
            width: 100% !important;
            object-fit: contain !important;
        }
        .eb-export-panel {
            margin: 0.35rem 0 0.55rem;
            padding: 0.65rem 0.55rem 0.25rem;
        }
        .eb-export-trail-wrap {
            margin-top: 0.35rem;
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


def _plan_snapshots(date_str: str) -> dict:
    plan = load_daily_meal_plan(date_str)
    if plan:
        return dict(plan.get("snapshots") or {})
    return dict(st.session_state.get("eb_plan_snapshots") or {})


def _menu_rows_for_ids(menu_ids: list[str], date_str: str | None = None) -> list[dict]:
    snapshots = _plan_snapshots(date_str) if date_str else {}
    rows: list[dict] = []
    for mid in menu_ids:
        row = get_menu_row(mid, snapshots)
        if row:
            rows.append(row)
    return rows


def _render_menu_summary(date_str: str, menu_ids: list[str]) -> None:
    if not menu_ids:
        st.info(f"{date_str} 暂无已保存的菜单记录。")
        return
    for row in _menu_rows_for_ids(menu_ids, date_str):
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
    from src.user_vault import notify_user_data_changed

    notify_user_data_changed()


def _record_shared_menus(day: str, menu_ids: list[str]) -> None:
    if menu_ids:
        record_menu_archive(day, menu_ids, is_shared=True)


def _show_sample_poster() -> bool:
    """Sample poster only before the user has ever generated one."""
    if user_has_generated_poster():
        return False
    if st.session_state.get("export_action_panel") == "poster":
        return False
    return _SAMPLE_POSTER.is_file()


def _render_default_poster() -> None:
    st.markdown('<div class="eb-poster-hero">', unsafe_allow_html=True)
    if st.session_state.get("poster_bytes"):
        _show_poster_image(st.session_state.poster_bytes)
    elif _show_sample_poster():
        _show_poster_image(str(_SAMPLE_POSTER))
    st.markdown("</div>", unsafe_allow_html=True)


def _render_poster_actions(date_str: str) -> None:
    if not st.session_state.get("poster_bytes"):
        return
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
            rows = _menu_rows_for_ids(ids, date_for_code)
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


def _render_poster_controls() -> None:
    from src.app_time import beijing_today, beijing_today_iso

    today = beijing_today()
    today_iso = beijing_today_iso()
    default_ids = primary_menu_ids_for_poster(today_iso) or _today_menu_ids()

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
        menu_ids = primary_menu_ids_for_poster(date_str) or menu_ids_for_date(date_str)

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
            photos.extend(f.getvalue() for f in uploaded[:2])
        for data in gallery_photos:
            if len(photos) >= 2:
                break
            photos.append(data)
        photos = photos[:2]

        snapshots = _plan_snapshots(date_str)
        meals = meals_for_poster(date_str, menu_ids)
        if not meals:
            st.error("未找到菜单数据，请先在「菜单」页确认今日就餐计划。")
            return
        try:
            with st.spinner("正在生成海报…"):
                png_bytes = generate_poster(
                    date_str=date_str,
                    meals=meals,
                    photos=photos,
                    snapshots=snapshots,
                )
        except Exception as exc:
            st.error(f"海报生成失败：{exc}")
            return
        if not png_bytes:
            st.error("海报生成失败，请稍后重试。")
            return
        if uploaded:
            save_uploads_to_library(uploaded, source="user")
        save_poster_state(date_str, png_bytes, menu_ids)
        st.session_state.poster_share_text = ""
        _append_poster_history(date_str, menu_ids)
        st.rerun()


def _render_poster_section() -> None:
    from src.app_time import beijing_today_iso

    today_iso = st.session_state.get("today_date", beijing_today_iso())
    restore_poster_for_display(today_iso)
    _render_default_poster()
    if st.session_state.get("poster_bytes"):
        _render_poster_actions(str(st.session_state.get("poster_date_str", today_iso)))
    if st.session_state.get("export_action_panel") == "poster":
        st.markdown('<div class="eb-export-panel">', unsafe_allow_html=True)
        _render_poster_controls()
        st.markdown("</div>", unsafe_allow_html=True)


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
            menu_row = get_menu_row(new_id, {})
            if menu_row:
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
            else:
                btn_col, _ = st.columns([1, 1])
                with btn_col:
                    if st.button("生成口令", key=f"trail_gen_{idx}_{date_str}", use_container_width=True):
                        rows = _menu_rows_for_ids(ids, date_str)
                        if rows:
                            code = encode_day_menu_share_text(date_str, rows)
                            item["share_text"] = code
                            history[idx] = item
                            st.session_state.poster_history = history
                            _record_shared_menus(date_str, ids)
                            st.rerun()
            if st.button("恢复此日海报", key=f"trail_restore_{idx}_{date_str}", use_container_width=True):
                restore_poster_for_display(date_str)
                st.rerun()


def _render_top_actions() -> None:
    if "export_action_panel" not in st.session_state:
        st.session_state.export_action_panel = None

    panel = st.session_state.export_action_panel
    st.markdown('<div class="eb-export-top-actions">', unsafe_allow_html=True)
    col_a, col_b = st.columns(2, gap="small")
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
    st.markdown("</div>", unsafe_allow_html=True)

    if panel == "import":
        st.markdown('<div class="eb-export-panel">', unsafe_allow_html=True)
        _render_import_panel()
        st.markdown("</div>", unsafe_allow_html=True)


def _render_trail_action() -> None:
    panel = st.session_state.get("export_action_panel")
    st.markdown('<div class="eb-export-trail-wrap eb-export-trail-action">', unsafe_allow_html=True)
    if st.button(
        "📤 海报分享轨迹",
        key="export_btn_trail",
        use_container_width=True,
        type="primary" if panel == "trail" else "secondary",
    ):
        st.session_state.export_action_panel = None if panel == "trail" else "trail"
        st.rerun()

    if panel == "trail":
        st.markdown('<div class="eb-export-panel">', unsafe_allow_html=True)
        _render_trail_panel()
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render() -> None:
    apply_gallery_pick_action()

    _inject_export_ui_css()

    from src.app_time import beijing_today_iso

    if st.session_state.pop("review_complete", False):
        st.session_state.export_action_panel = "poster"
        st.success("回顾已完成 · 上传实拍，生成今日全日生活志海报吧。")

    if "poster_history" not in st.session_state:
        st.session_state.poster_history = []
    if "poster_cache" not in st.session_state:
        st.session_state.poster_cache = {}
    if "poster_b64_cache" not in st.session_state:
        st.session_state.poster_b64_cache = {}

    restore_poster_for_display(st.session_state.get("today_date", beijing_today_iso()))

    _render_top_actions()
    _render_poster_section()
    _render_trail_action()
