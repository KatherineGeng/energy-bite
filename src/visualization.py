"""PIL-based 9:16 daily life poster for Energy Bite V2."""

from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from src.constants import POSTER_HEIGHT, POSTER_WIDTH
from src.database import get_ingredient_map, parse_energy_tags, parse_list_field

# Canvas
BG_HEX = "#F9F8F6"
BG_COLOR = (249, 248, 246)
LINE_COLOR = (220, 218, 214)
TEXT_DARK = (38, 38, 38)
TEXT_MID = (110, 108, 104)
TEXT_LIGHT = (150, 148, 144)
ACCENT = (141, 163, 153)
PILL_BG = (237, 242, 238)
PILL_TEXT = (94, 120, 108)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LIFESTYLE_LOCAL_CANDIDATES = [
    PROJECT_ROOT / "assets" / "placeholders" / "lifestyle_default.jpg",
    PROJECT_ROOT / "pictures" / "Pic 1.jpg",
]
LIFESTYLE_PLACEHOLDER_URL = (
    "http://googleusercontent.com/image_collection/image_retrieval/13967363910131595220"
)

FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]

LEFT_MARGIN = 72
RIGHT_MARGIN = 72
LABEL_COL_W = 96
TITLE_X = LEFT_MARGIN + LABEL_COL_W
DETAIL_X = LEFT_MARGIN + 20
CONTENT_W = POSTER_WIDTH - LEFT_MARGIN - RIGHT_MARGIN


def _y(ratio: float) -> int:
    return int(POSTER_HEIGHT * ratio)


def _load_font(size: int, index: int = 0) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size=size, index=index)
            except OSError:
                try:
                    return ImageFont.truetype(path, size=size)
                except OSError:
                    continue
    return ImageFont.load_default()


def _text_size(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    if not text:
        return 0, 0
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _wrap_by_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    font,
    max_width: int,
) -> list[str]:
    if not text:
        return []
    lines: list[str] = []
    current = ""
    for ch in text:
        trial = current + ch
        tw, _ = _text_size(draw, trial, font)
        if tw <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def _format_date(date_str: str) -> str:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y.%m.%d")
    except ValueError:
        return date_str


def _ingredient_line(menu_row: dict, ingredient_map: dict[str, dict]) -> str:
    ids = parse_list_field(menu_row.get("ingredient_ids", ""))
    names: list[str] = []
    for ing_id in ids:
        ing = ingredient_map.get(ing_id)
        if ing:
            names.append(str(ing.get("name", ing_id)))
    if not names:
        return ""
    return f"({' | '.join(names)})"


def _collect_day_tags(meals: list[dict]) -> list[str]:
    tags: list[str] = []
    seen: set[str] = set()
    for meal in meals:
        for tag in parse_energy_tags(meal.get("energy_tags", "")):
            if tag not in seen:
                seen.add(tag)
                tags.append(tag)
    return tags


def _derive_theme(tags: list[str]) -> str:
    if not tags:
        return "神经抗炎 · 代谢重启"
    return " · ".join(tags[:2])


def _center_crop_aspect(img: Image.Image, aspect: float) -> Image.Image:
    w, h = img.size
    current = w / h
    if current > aspect:
        new_w = int(h * aspect)
        left = (w - new_w) // 2
        box = (left, 0, left + new_w, h)
    else:
        new_h = int(w / aspect)
        top = (h - new_h) // 2
        box = (0, top, w, top + new_h)
    return img.crop(box)


def _fit_crop(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    aspect = target_w / target_h
    cropped = _center_crop_aspect(img, aspect)
    return cropped.resize(size, Image.Resampling.LANCZOS)


def _open_photo(source: Any) -> Image.Image:
    if isinstance(source, Image.Image):
        return source.convert("RGB")
    if isinstance(source, (bytes, bytearray)):
        return Image.open(io.BytesIO(source)).convert("RGB")
    return Image.open(source).convert("RGB")


def _draw_hline(draw: ImageDraw.ImageDraw, y: int) -> None:
    draw.line([(LEFT_MARGIN, y), (POSTER_WIDTH - RIGHT_MARGIN, y)], fill=LINE_COLOR, width=1)


def _draw_module_a(draw: ImageDraw.ImageDraw, date_str: str, theme: str) -> None:
    date_font = _load_font(34)
    brand_font = _load_font(22)
    theme_font = _load_font(26)

    y_top = _y(0.05)
    draw.text((LEFT_MARGIN, y_top), _format_date(date_str), fill=TEXT_DARK, font=date_font)
    draw.text((LEFT_MARGIN, y_top + 44), "THE ENERGY BITE", fill=TEXT_MID, font=brand_font)

    theme_lines = _wrap_by_width(draw, theme, theme_font, max_width=360)
    theme_y = y_top + 4
    for line in theme_lines:
        draw.text((POSTER_WIDTH - RIGHT_MARGIN, theme_y), line, fill=TEXT_DARK, font=theme_font, anchor="ra")
        _, lh = _text_size(draw, line, theme_font)
        theme_y += lh + 6

    _draw_hline(draw, _y(0.12))


def _draw_module_b(draw: ImageDraw.ImageDraw, meals: list[dict], ingredient_map: dict) -> None:
    label_font = _load_font(28)
    name_font = _load_font(32)
    detail_font = _load_font(24)

    slots = [
        ("晨", "早餐"),
        ("午", "午餐"),
        ("晚", "晚餐"),
    ]
    meal_by_type = {m.get("meal_type"): m for m in meals}
    y = _y(0.15)
    title_max_w = POSTER_WIDTH - TITLE_X - RIGHT_MARGIN
    detail_max_w = POSTER_WIDTH - DETAIL_X - RIGHT_MARGIN

    for label, meal_type in slots:
        meal = meal_by_type.get(meal_type)
        name = meal.get("menu_name", "—") if meal else "—"
        name_lines = _wrap_by_width(draw, name, name_font, title_max_w)

        if name_lines:
            _, title_h = _text_size(draw, name_lines[0], name_font)
            _, label_h = _text_size(draw, label, label_font)
            label_y = y + max(0, (title_h - label_h) // 2)
            draw.text((LEFT_MARGIN, label_y), label, fill=TEXT_MID, font=label_font)

        for line in name_lines:
            draw.text((TITLE_X, y), line, fill=TEXT_DARK, font=name_font)
            _, lh = _text_size(draw, line, name_font)
            y += lh + 4

        y += 6
        if meal:
            detail = _ingredient_line(meal, ingredient_map)
            if detail:
                for line in _wrap_by_width(draw, detail, detail_font, detail_max_w):
                    draw.text((DETAIL_X, y), line, fill=TEXT_LIGHT, font=detail_font)
                    _, lh = _text_size(draw, line, detail_font)
                    y += lh + 4

        y += int(POSTER_HEIGHT * 0.028)

    _draw_hline(draw, _y(0.42))


def _load_lifestyle_placeholder() -> Image.Image | None:
    import urllib.request

    for path in LIFESTYLE_LOCAL_CANDIDATES:
        if path.exists():
            return Image.open(path).convert("RGB")

    try:
        with urllib.request.urlopen(LIFESTYLE_PLACEHOLDER_URL, timeout=8) as resp:
            return Image.open(io.BytesIO(resp.read())).convert("RGB")
    except Exception:
        return None


def _draw_module_c(canvas: Image.Image, photos: list[Any]) -> None:
    zone_top = _y(0.45)
    zone_bottom = _y(0.82)
    zone_h = zone_bottom - zone_top

    effective_photos = list(photos or [])
    if not effective_photos:
        placeholder = _load_lifestyle_placeholder()
        if placeholder is not None:
            effective_photos = [placeholder]

    if not effective_photos:
        draw = ImageDraw.Draw(canvas)
        quote_font = _load_font(30, index=0)
        quote = "*用智性饮食，构筑未来身心秩序。*"
        draw.text(
            (POSTER_WIDTH // 2, zone_top + zone_h // 2),
            quote,
            fill=TEXT_LIGHT,
            font=quote_font,
            anchor="mm",
        )
        return

    if len(effective_photos) == 1:
        img = _fit_crop(_open_photo(effective_photos[0]), (720, 540))
        x = POSTER_WIDTH - RIGHT_MARGIN - 720
        y = zone_top + (zone_h - 540) // 2
        canvas.paste(img, (x, y))
        return

    left_img = _fit_crop(_open_photo(effective_photos[0]), (420, 560))
    right_img = _fit_crop(_open_photo(effective_photos[1]), (380, 380))
    left_x = LEFT_MARGIN
    right_x = POSTER_WIDTH - RIGHT_MARGIN - 380
    left_y = zone_top + (zone_h - 560) // 2
    right_y = left_y + 42
    canvas.paste(left_img, (left_x, left_y))
    canvas.paste(right_img, (right_x, right_y))


def _pill_width(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _draw_module_d(draw: ImageDraw.ImageDraw, tags: list[str]) -> None:
    pill_font = _load_font(24)
    footer_font = _load_font(22)

    display_tags = [f"#{t.replace(' ', '')}" for t in tags[:5]]
    if not display_tags:
        display_tags = ["#脑力续航", "#代谢平衡", "#从容有序"]

    pad_x, pad_y = 22, 12
    gap = 16
    pill_specs: list[tuple[str, int, int, int]] = []
    for tag in display_tags:
        tw, th = _pill_width(draw, tag, pill_font)
        pill_w = tw + pad_x * 2
        pill_h = th + pad_y * 2
        pill_specs.append((tag, pill_w, pill_h, tw))

    row_w = sum(w for _, w, _, _ in pill_specs) + gap * (len(pill_specs) - 1)
    x = max(LEFT_MARGIN, (POSTER_WIDTH - row_w) // 2)
    row_y = _y(0.865)

    for tag, pill_w, pill_h, tw in pill_specs:
        draw.rounded_rectangle(
            (x, row_y, x + pill_w, row_y + pill_h),
            radius=18,
            fill=PILL_BG,
        )
        draw.text((x + pad_x, row_y + pad_y - 2), tag, fill=PILL_TEXT, font=pill_font)
        x += pill_w + gap

    draw.text(
        (POSTER_WIDTH // 2, _y(0.93)),
        "每一口，都是对未来身心秩序的深耕。",
        fill=TEXT_MID,
        font=footer_font,
        anchor="mm",
    )


def generate_daily_poster(
    date_str: str,
    meals: list[dict],
    photos: list[Any] | None = None,
    theme: str = "",
) -> bytes:
    """Compose full-day 9:16 poster. photos: 0–2 PIL Image / bytes / paths."""
    canvas = Image.new("RGB", (POSTER_WIDTH, POSTER_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(canvas)

    ingredient_map = get_ingredient_map()
    tags = _collect_day_tags(meals)
    header_theme = theme or _derive_theme(tags)

    _draw_module_a(draw, date_str, header_theme)
    _draw_module_b(draw, meals, ingredient_map)
    _draw_module_c(canvas, list(photos or [])[:2])
    draw = ImageDraw.Draw(canvas)
    _draw_module_d(draw, tags)

    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


def meals_for_poster_from_ids(menu_ids: list[str]) -> list[dict]:
    from src.database import get_menu_by_id

    meals: list[dict] = []
    for menu_id in menu_ids:
        row = get_menu_by_id(menu_id)
        if row:
            meals.append(row)
    return meals
