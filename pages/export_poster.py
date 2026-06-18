"""Sharing & collection — Energy Bite 4.0."""

from __future__ import annotations

from datetime import date

import streamlit as st

from src.database import (
    append_menu_from_share,
    get_log_history_for_share,
    get_menu_by_id,
    get_menu_weight,
    init_database,
    load_favorites_dishes,
    load_favorites_menus,
    load_menus,
)
from src.export import generate_poster
from src.share_code import ShareCodeError, decode_share_code, encode_share_code
from src.theme import LIFESTYLE_PLACEHOLDER_URL, page_title, section_title


def _final_menu_ids() -> list[str]:
    return list(st.session_state.get("final_daily_list", []))


def _render_poster_tab() -> None:
    if not _final_menu_ids():
        st.info("请先在【晨间餐饮】确认今日就餐计划。")
        return

    selected_date = st.date_input("选择日期", value=date.today(), key="export_date")
    date_str = selected_date.isoformat()

    uploaded = st.file_uploader(
        "上传今日实拍餐食（支持1-2张），生成专属全日生活志海报",
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

    if st.button("生成海报", type="primary", use_container_width=True, key="gen_poster"):
        photos = [f.getvalue() for f in uploaded] if uploaded else []
        png_bytes = generate_poster(
            date_str=date_str,
            menu_ids=_final_menu_ids(),
            photos=photos,
        )
        st.session_state.poster_bytes = png_bytes
        st.session_state.poster_filename = f"jianyu_{date_str}.png"
        st.session_state.show_share_guide = False

    if st.session_state.get("poster_bytes"):
        st.image(st.session_state.poster_bytes, caption="全日生活志海报预览", width=720)
        dl_col, guide_col = st.columns(2)
        with dl_col:
            st.download_button(
                "保存至本地",
                data=st.session_state.poster_bytes,
                file_name=st.session_state.get("poster_filename", "jianyu_poster.png"),
                mime="image/png",
                use_container_width=True,
                key="download_poster",
            )
        with guide_col:
            if st.button("复制分享指南", use_container_width=True, key="share_guide_btn"):
                st.session_state.show_share_guide = True
        if st.session_state.get("show_share_guide"):
            st.success("已保存海报，可长按图片保存并发送给微信好友")


def _render_history_share_tab() -> None:
    st.caption("从回顾历史中，分享效果最好的简愈搭配。")

    history = get_log_history_for_share()
    if history.empty:
        st.info("暂无历史记录。完成一次「晚间回顾」后，即可在此分享。")
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


def _render_favorites_tab() -> None:
    dishes = load_favorites_dishes()
    menus = load_favorites_menus()
    all_menus = load_menus()
    name_map = {r["menu_id"]: r["menu_name"] for _, r in all_menus.iterrows()} if not all_menus.empty else {}

    st.markdown("**❤️ 收藏菜品**")
    if dishes.empty:
        st.caption("暂无收藏菜品")
    else:
        for _, row in dishes.iterrows():
            st.write(f"· {name_map.get(row['menu_id'], row['menu_id'])}（{row['date']}）")

    st.markdown("**🌟 收藏全天菜单**")
    if menus.empty:
        st.caption("暂无收藏组合")
    else:
        for _, row in menus.iterrows():
            ids = str(row["menu_ids"]).split("|")
            names = " · ".join(name_map.get(mid, mid) for mid in ids)
            st.write(f"· {row['date']}：{names}")


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
    menus = load_menus()

    page_title("fa-share-nodes", "收藏分享")

    if st.session_state.pop("review_complete", False):
        st.success("晚间回顾已完成 · 上传实拍，生成今日全日生活志海报吧。")

    if menus.empty:
        st.warning("菜单库为空。")
        return

    tab1, tab2, tab3, tab4 = st.tabs(["📸 生活志海报", "📤 历史分享", "❤️ 我的收藏", "📥 导入菜单"])

    with tab1:
        _render_poster_tab()

    with tab2:
        _render_history_share_tab()

    with tab3:
        _render_favorites_tab()

    with tab4:
        _render_import_tab()
