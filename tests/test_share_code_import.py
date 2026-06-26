"""Share-code parsing tests."""

from src.share_code import PREFIX, SUFFIX, decode_share_code, parse_share_paste_entries


def test_parse_day_share_block():
    text = """【2026-06-26 简愈一人食】
午餐·抗炎三文鱼配低GI碳水
￥MENU:ING_004|ING_005:脑力续航·降胆固醇:0.00￥
晚餐·姜黄香煎豆腐杂粮饭
￥MENU:ING_005|ING_007:代谢重启·植物雌激素:0.00￥"""
    entries = parse_share_paste_entries(text)
    assert len(entries) == 2
    assert entries[0].meal_type == "午餐"
    assert entries[0].menu_name == "抗炎三文鱼配低GI碳水"
    assert entries[1].meal_type == "晚餐"
    assert entries[1].menu_name == "姜黄香煎豆腐杂粮饭"


def test_decode_single_share_code():
    code = f"{PREFIX}ING_001|ING_002:快速供能·肠脑舒缓:0.85{SUFFIX}"
    payload = decode_share_code(code)
    assert payload.ingredient_ids == ["ING_001", "ING_002"]
    assert payload.energy_tags == "快速供能·肠脑舒缓"
    assert payload.estimated_score == 0.85
