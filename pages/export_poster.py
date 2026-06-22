"""Sharing & collection — 简愈一人食 4.7."""

from __future__ import annotations

from datetime import date

import streamlit as st

from src.database import (
    append_menu_from_share,
    get_log_history_for_share,
    get_menu_by_id,
    get_menu_weight,
    init_database,
    load_daily_meal_plan,
    load_favorites_dishes,
    load_favorites_menus,
    load_menus,
)
from src.export import generate_poster
from src.meal_plan_dates import markers_with_today
from src.session_hydrate import hydrate_today_state, menu_ids_for_date
from src.share_code import ShareCodeError, decode_share_code, encode_day_menu_share_text, encode_share_code
from src.theme import LIFESTYLE_PLACEHOLDER_URL, page_title



TAB_OPTIONS: list[tuple[str, str]] = [

    ("poster", "📸 生活志海报"),

    ("past", "📅 按日期菜单"),

    ("history", "📤 历史分享"),

    ("favorites", "❤️ 收藏菜单"),

    ("import", "📥 导入菜单"),

]

TAB_LABEL_MAP = dict(TAB_OPTIONS)





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

    today = date.today()

    today_iso = today.isoformat()

    default_ids = _today_menu_ids()



    if default_ids:

        st.caption("默认使用「今日菜单」中当前/已确认的就餐计划。")

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

        if st.button("过往菜单海报", use_container_width=True, key="goto_past_menus"):

            st.session_state.export_tab_key = "past"

            st.rerun()



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

        st.markdown(

            f"""

            <p style="font-size:0.85rem;color:#64748B;margin-bottom:0.35rem;">

            <i class="fa-solid fa-camera"></i> 未上传时将使用系统默认生活方式图

            </p>

            <img src="{LIFESTYLE_PLACEHOLDER_URL}" style="width:100%;max-width:420px;border-radius:12px;

            border:1px solid rgba(141,163,153,0.3);" alt="默认生活方式占位图"/>

            """,

            unsafe_allow_html=True,

        )

    if uploaded and len(uploaded) > 2:

        st.warning("最多上传 2 张照片，已自动使用前 2 张。")

        uploaded = uploaded[:2]



    if st.button(

        "生成海报",

        type="primary",

        use_container_width=True,

        key="gen_poster",

        disabled=not menu_ids,

    ):

        photos = [f.getvalue() for f in uploaded] if uploaded else []

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

        st.image(st.session_state.poster_bytes, caption="全日生活志海报预览", width=720)

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





def _render_past_menus_tab() -> None:
    st.caption("点击日历中有圆点的日期，查看当日菜单并生成分享口令。")

    today_iso = st.session_state.get("today_date", date.today().isoformat())
    today_ids = _today_menu_ids()
    markers = markers_with_today(
        today_iso,
        today_has_menu=bool(today_ids),
        today_confirmed=bool(st.session_state.get("menu_locked")),
    )

    if not markers:
        st.info("暂无历史菜单。在「菜单」页生成或确认就餐计划后会自动保存。")
        return

    if "past_menu_date" not in st.session_state:
        default = today_iso if today_iso in markers else sorted(markers.keys(), reverse=True)[0]
        st.session_state.past_menu_date = default

    # Native date picker — reliable on mobile (custom calendar component removed)
    marked_dates = sorted(markers.keys(), reverse=True)
    default_date = date.fromisoformat(st.session_state.past_menu_date)
    picked_date = st.date_input(
        "选择日期（● 已确认 ○ 草稿见下方列表）",
        value=default_date,
        min_value=date.fromisoformat(marked_dates[-1]),
        max_value=date.fromisoformat(marked_dates[0]),
        key="past_menu_calendar",
    )
    pick_date = picked_date.isoformat()
    if pick_date != st.session_state.past_menu_date:
        st.session_state.past_menu_date = pick_date
        st.session_state.day_share_text = ""

    st.caption("有菜单的日期：" + " · ".join(
        f"{d}({'●' if markers[d] == 'confirmed' else '○'})" for d in marked_dates[:12]
    ))

    saved = load_daily_meal_plan(pick_date)
    menu_ids = saved["menu_ids"] if saved else menu_ids_for_date(pick_date)
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

    st.caption("从回顾历史中，分享效果最好的简愈搭配。")



    history = get_log_history_for_share()

    if history.empty:

        st.info("暂无历史记录。完成一次「回顾」后，即可在此分享。")

        return



    for _, row in history.head(20).iterrows():

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



    page_title("fa-share-nodes", "分享")



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


