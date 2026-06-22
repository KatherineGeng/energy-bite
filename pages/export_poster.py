"""Sharing & collection — 简愈一人食 4.8."""

from __future__ import annotations

from datetime import date

import streamlit as st

from src.database import (
    append_menu_from_share,
    dates_with_menus,
    get_log_dates,
    get_log_history_for_share,
    get_menu_by_id,
    get_menu_weight,
    init_database,
    all_menu_ids_for_date,
    load_favorites_dishes,
    load_favorites_menus,
    load_menus,
    record_menu_archive,
    search_archive_menu_ids,
)
from src.export import generate_poster
from src.image_library import render_gallery_picker, save_uploads_to_library
from src.menu_calendar_ui import render_menu_calendar
from src.query_nav import qp_first
from src.session_hydrate import hydrate_today_state, menu_ids_for_date
from src.share_code import ShareCodeError, decode_share_code, encode_day_menu_share_text, encode_share_code

TAB_OPTIONS: list[tuple[str, str]] = [
    ("poster", "📸 生活志海报"),
    ("past", "📅 按日期菜单"),
    ("history", "📤 历史分享"),
    ("favorites", "❤️ 收藏菜单"),
    ("import", "📥 导入菜单"),
]

TAB_LABEL_MAP = dict(TAB_OPTIONS)

_CAL_EXTRA = {"nav": "export"}


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



def _render_poster_tab() -> None:
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
        </style>
        """,
        unsafe_allow_html=True,
    )

    today = date.today()
    today_iso = today.isoformat()
    default_ids = _today_menu_ids()

    if default_ids:
        st.markdown(
            '<p class="eb-poster-default-hint">默认使用「今日菜单」中当前/已确认的就餐计划。</p>',
            unsafe_allow_html=True,
        )
    else:
        st.info("请先在「菜单」页确认今日就餐计划，或选择下方日期查看过往菜单。")

    col1, col2 = st.columns(2)
    with col1:
        selected_date = st.date_input(
            "海报日期",
            value=today,
            key="export_poster_date",
        )
    with col2:
        st.link_button(
            "过往菜单海报",
            url="?nav=export&export_tab=past",
            use_container_width=True,
        )

    date_str = selected_date.isoformat()
    if date_str == today_iso and default_ids:
        menu_ids = default_ids
    else:
        menu_ids = menu_ids_for_date(date_str)

    if menu_ids:
        _render_menu_summary(date_str, menu_ids)

    uploaded = st.file_uploader(
        "上传实拍餐食（支持1-2张），生成专属全日生活志海报",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="meal_photos",
    )
    if not uploaded:
        st.caption("未上传时可从下方 App 图片库选择，或使用系统默认生活方式图")
    if uploaded and len(uploaded) > 2:
        st.warning("最多上传 2 张照片，已自动使用前 2 张。")
        uploaded = uploaded[:2]

    gallery_photos = render_gallery_picker("poster_gallery", max_select=2)

    if st.button(
        "生成海报",
        type="primary",
        use_container_width=True,
        key="gen_poster",
        disabled=not menu_ids,
    ):
        photos: list[bytes] = []
        if uploaded:
            save_uploads_to_library(uploaded, source="user")
            photos.extend(f.getvalue() for f in uploaded[:2])
        for data in gallery_photos:
            if len(photos) >= 2:
                break
            photos.append(data)
        photos = photos[:2]
        png_bytes = generate_poster(
            date_str=date_str,
            menu_ids=menu_ids,
            photos=photos,
        )
        st.session_state.poster_bytes = png_bytes
        st.session_state.poster_filename = f"jianyu_{date_str}.png"
        st.session_state.poster_menu_ids = menu_ids
        st.session_state.poster_date_str = date_str
        st.session_state.poster_share_text = ""

    if st.session_state.get("poster_bytes"):
        st.image(st.session_state.poster_bytes, caption="全日生活志海报预览", use_container_width=True)
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
                    st.session_state.poster_share_text = encode_day_menu_share_text(date_for_code, rows)
                    _record_shared_menus(date_for_code, ids)
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


def _record_shared_menus(day: str, menu_ids: list[str]) -> None:
    if menu_ids:
        record_menu_archive(day, menu_ids, is_shared=True)


def _render_past_menus_tab() -> None:
    st.caption("按日期查看菜单；深色日期可点击，灰色日期无记录。")

    search = st.text_input("搜索菜品名称", placeholder="输入菜名关键字", key="archive_search")
    if search.strip():
        hits = search_archive_menu_ids(search.strip())
        if hits:
            st.caption("搜索结果：")
            _render_menu_summary("搜索", hits)
        else:
            st.info("未找到匹配的菜品。")

    marked = dates_with_menus()
    if not marked:
        st.info("暂无历史菜单。在「菜单」页生成或确认就餐计划后会自动保存。")
        return

    pick_date = qp_first("past_date") or st.session_state.get("past_menu_date")
    if not pick_date or pick_date not in marked:
        today_iso = st.session_state.get("today_date", date.today().isoformat())
        pick_date = today_iso if today_iso in marked else sorted(marked, reverse=True)[0]

    pick_date = render_menu_calendar(
        marked,
        pick_date,
        pick_key="past_date",
        month_key="past_month",
        extra_params={**_CAL_EXTRA, "export_tab": "past"},
    )
    prev_date = st.session_state.get("past_menu_date")
    st.session_state.past_menu_date = pick_date
    if prev_date and prev_date != pick_date:
        st.session_state.day_share_text = ""

    menu_ids = all_menu_ids_for_date(pick_date)
    if not menu_ids:
        menu_ids = menu_ids_for_date(pick_date)
    rows = _menu_rows_for_ids(menu_ids)

    if not menu_ids:
        st.info(f"{pick_date} 暂无已保存的菜单记录。")
        return

    st.markdown("---")
    _render_menu_summary(pick_date, menu_ids)

    if not rows:
        return

    if st.button("生成当日分享口令", type="primary", use_container_width=True, key="gen_day_share"):
        st.session_state.day_share_text = encode_day_menu_share_text(pick_date, rows)
        _record_shared_menus(pick_date, menu_ids)

    if st.session_state.get("day_share_text"):
        st.text_area(
            "分享口令（复制发送给好友）",
            value=st.session_state.day_share_text,
            height=160,
            key="day_share_display",
        )

    st.markdown("**单道菜口令**")
    for row in rows:
        score = get_menu_weight(row["menu_id"])
        code = encode_share_code(
            ingredient_ids=row["ingredient_ids"],
            energy_tags=row["energy_tags"],
            estimated_score=score,
        )
        with st.expander(f"{row.get('meal_type', '')} · {row['menu_name']}"):
            st.code(code, language=None)


def _render_history_share_tab() -> None:
    st.caption("按日期查看回顾记录，分享效果最好的简愈搭配。")

    marked = get_log_dates()
    if not marked:
        st.info("暂无历史记录。完成一次「回顾」后，即可在此分享。")
        return

    pick_date = qp_first("hist_date") or st.session_state.get("hist_menu_date")
    if not pick_date or pick_date not in marked:
        pick_date = sorted(marked, reverse=True)[0]

    pick_date = render_menu_calendar(
        marked,
        pick_date,
        pick_key="hist_date",
        month_key="hist_month",
        extra_params={**_CAL_EXTRA, "export_tab": "history"},
    )
    st.session_state.hist_menu_date = pick_date

    history = get_log_history_for_share()
    day_logs = history[history["date"].astype(str) == pick_date]
    if day_logs.empty:
        st.info(f"{pick_date} 暂无回顾记录。")
        return

    st.markdown("---")
    for _, row in day_logs.iterrows():
        with st.container(border=True):
            st.markdown(f"**{row['label']}**")
            st.caption(
                f"从容度 {int(row['operation_score'])}/5 · NPS {int(row['taste_score'])}/5 · "
                f"{'已收藏' if row['is_favorited'] else '未收藏'}"
            )
            if st.button(f"生成口令", key=f"share_hist_{row['log_id']}", use_container_width=True):
                menu_row = get_menu_by_id(row["menu_id"])
                if menu_row:
                    score = get_menu_weight(row["menu_id"])
                    st.session_state.history_share_code = encode_share_code(
                        ingredient_ids=menu_row["ingredient_ids"],
                        energy_tags=menu_row["energy_tags"],
                        estimated_score=score,
                    )
                    _record_shared_menus(str(row["date"]), [str(row["menu_id"])])

    if st.session_state.get("history_share_code"):
        st.text_area(
            "分享口令（复制发送给好友）",
            value=st.session_state.history_share_code,
            height=72,
            key="history_share_code_display",
        )


def _render_fav_menus_subtab() -> None:
    menus = load_favorites_menus()
    all_menus = load_menus()
    name_map = {r["menu_id"]: r["menu_name"] for _, r in all_menus.iterrows()} if not all_menus.empty else {}

    if menus.empty:
        st.caption("暂无收藏组合 · 可在「菜单」页点击「收藏此菜单」")
        return

    for _, row in menus.iterrows():
        ids = [x for x in str(row["menu_ids"]).split("|") if x]
        names = " · ".join(name_map.get(mid, mid) for mid in ids)
        st.markdown(f"**{row['date']}**")
        st.caption(names)
        st.divider()


def _render_fav_dishes_subtab() -> None:
    dishes = load_favorites_dishes()
    all_menus = load_menus()
    name_map = {r["menu_id"]: r["menu_name"] for _, r in all_menus.iterrows()} if not all_menus.empty else {}

    if dishes.empty:
        st.caption("暂无收藏菜品 · 可在「回顾」页收藏单道菜")
        return

    for _, row in dishes.iterrows():
        st.write(f"· {name_map.get(row['menu_id'], row['menu_id'])}（{row['date']}）")


def _render_favorites_tab() -> None:
    tab_menus, tab_dishes = st.tabs(["🌟 全天菜单", "❤️ 单个菜品"])
    with tab_menus:
        _render_fav_menus_subtab()
    with tab_dishes:
        _render_fav_dishes_subtab()


def _render_import_tab() -> None:
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


def render() -> None:
    init_database()
    hydrate_today_state()
    menus = load_menus()

    if st.session_state.pop("review_complete", False):
        st.success("回顾已完成 · 上传实拍，生成今日全日生活志海报吧。")

    if menus.empty:
        st.warning("菜单库为空。")
        return

    if "export_tab_key" not in st.session_state:
        st.session_state.export_tab_key = "poster"

    tab_keys = [k for k, _ in TAB_OPTIONS]
    st.radio(
        "分享分区",
        options=tab_keys,
        format_func=lambda k: TAB_LABEL_MAP[k],
        horizontal=True,
        key="export_tab_key",
        label_visibility="collapsed",
    )

    active = st.session_state.export_tab_key
    if active == "poster":
        _render_poster_tab()
    elif active == "past":
        _render_past_menus_tab()
    elif active == "history":
        _render_history_share_tab()
    elif active == "favorites":
        _render_favorites_tab()
    elif active == "import":
        _render_import_tab()
