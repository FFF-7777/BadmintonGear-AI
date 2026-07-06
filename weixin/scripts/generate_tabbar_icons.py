"""生成微信小程序 TabBar 高清图标 (162x162, 2x 视网膜)"""
from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 162
OUT_DIR = Path(__file__).resolve().parent.parent / "images"
GRAY = (153, 153, 153, 255)
BLUE = (64, 158, 255, 255)
STROKE = 7


def new_canvas():
    return Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))


def draw_home(draw, color, filled=False):
    cx = SIZE // 2
    roof = [(cx, 30), (38, 70), (124, 70)]
    body = (50, 70, 112, 132)
    if filled:
        draw.polygon(roof, fill=color)
        draw.rectangle(body, fill=color)
        draw.rectangle((74, 92, 88, 132), fill=(255, 255, 255, 255))
    else:
        draw.polygon(roof, outline=color, width=STROKE)
        draw.rounded_rectangle(body, radius=6, outline=color, width=STROKE)
        draw.line([(81, 94), (81, 132)], fill=color, width=STROKE)


def draw_category(draw, color, filled=False):
    gap, pad, r = 10, 34, 8
    cell = (SIZE - pad * 2 - gap) // 2
    for row in range(2):
        for col in range(2):
            x1 = pad + col * (cell + gap)
            y1 = pad + row * (cell + gap)
            box = (x1, y1, x1 + cell, y1 + cell)
            if filled:
                draw.rounded_rectangle(box, radius=r, fill=color)
            else:
                draw.rounded_rectangle(box, radius=r, outline=color, width=STROKE)


def draw_cart(draw, color, filled=False):
    basket = [(44, 54), (58, 32), (104, 32), (118, 54), (110, 112), (52, 112)]
    if filled:
        draw.polygon(basket, fill=color)
        draw.ellipse((50, 114, 70, 134), fill=(255, 255, 255, 255))
        draw.ellipse((92, 114, 112, 134), fill=(255, 255, 255, 255))
        draw.ellipse((54, 118, 66, 130), fill=color)
        draw.ellipse((96, 118, 108, 130), fill=color)
    else:
        draw.line([(58, 32), (104, 32)], fill=color, width=STROKE)
        draw.line([(44, 54), (58, 32)], fill=color, width=STROKE)
        draw.line([(118, 54), (104, 32)], fill=color, width=STROKE)
        draw.line([(44, 54), (118, 54)], fill=color, width=STROKE)
        draw.line([(52, 112), (44, 54)], fill=color, width=STROKE)
        draw.line([(110, 112), (118, 54)], fill=color, width=STROKE)
        draw.line([(52, 112), (110, 112)], fill=color, width=STROKE)
        draw.ellipse((50, 114, 70, 134), outline=color, width=STROKE)
        draw.ellipse((92, 114, 112, 134), outline=color, width=STROKE)


def draw_user(draw, color, filled=False):
    head = (58, 34, 104, 80)
    if filled:
        draw.ellipse(head, fill=color)
        draw.pieslice((38, 82, 124, 156), start=200, end=-20, fill=color)
    else:
        draw.ellipse(head, outline=color, width=STROKE)
        draw.arc((40, 84, 122, 152), start=200, end=-20, fill=color, width=STROKE)


ICONS = {
    "home": draw_home,
    "category": draw_category,
    "cart": draw_cart,
    "user": draw_user,
}


def save_icon(name, color, suffix, filled=False):
    img = new_canvas()
    draw = ImageDraw.Draw(img)
    ICONS[name](draw, color, filled=filled)
    path = OUT_DIR / f"{name}{suffix}.png"
    img.save(path, "PNG", optimize=True)
    print(f"saved {path.name} ({path.stat().st_size} bytes)")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name in ICONS:
        save_icon(name, GRAY, "", filled=False)
        save_icon(name, BLUE, "-active", filled=True)


if __name__ == "__main__":
    main()
