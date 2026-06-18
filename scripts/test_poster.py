"""Generate sample V2 poster using pictures/ test assets."""

from __future__ import annotations

from pathlib import Path

from src.database import init_database
from src.export import generate_poster

PROJECT = Path(__file__).resolve().parent.parent
PICTURES = PROJECT / "pictures"
OUT = PROJECT / "pictures" / "poster_v2_test.png"


def main() -> None:
    init_database(force=False)
    photos = []
    for name in ["Pic 1.jpg", "pic 2.png"]:
        path = PICTURES / name
        if path.exists():
            photos.append(path)

    menu_ids = ["MENU_001", "MENU_002", "MENU_003"]
    png = generate_poster(
        date_str="2026-06-18",
        menu_ids=menu_ids,
        photos=photos,
    )
    OUT.write_bytes(png)
    print(f"Saved: {OUT} ({len(png)} bytes, {len(photos)} photos)")


if __name__ == "__main__":
    main()
