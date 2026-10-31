"""Small demo household catalogue with labelled product illustrations."""
from urllib.parse import quote

_ROWS = [
    ("flash", "Flash surface cleaner", "surface cleaner", "blue", "bottle", "daughter", "2026-10-25"),
    ("persil", "Persil laundry detergent", "laundry detergent", "white", "bottle", "son", "2026-10-20"),
    ("comfort", "Comfort fabric conditioner", "laundry detergent", "blue", "bottle", "son", "2026-10-18"),
    ("fairy", "Fairy dish soap", "dish soap", "green", "bottle", "daughter", "2026-10-24"),
    ("harpic", "Harpic toilet cleaner", "toilet cleaner", "blue", "angled bottle", "son", "2026-10-15"),
    ("cravendale", "Cravendale milk", "milk", "white", "bottle", "daughter", "2026-10-28"),
    ("yorkshire", "Yorkshire tea", "tea", "red", "box", "daughter", "2026-10-10"),
    ("twinings", "Twinings green tea", "tea", "green", "box", "son", "2026-10-12"),
    ("dove", "Dove shampoo", "personal care", "white", "bottle", "daughter", "2026-10-05"),
    ("carex", "Carex hand wash", "personal care", "pink", "pump bottle", "son", "2026-10-22"),
]


def illustration(brand, colour, shape):
    radius = 0 if shape == "box" else 35
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400">'
           f'<rect width="400" height="400" fill="white"/><rect x="100" y="50" width="200" height="250" rx="{radius}" fill="{colour}" stroke="black"/>'
           f'<rect x="105" y="140" width="190" height="70" fill="white"/>'
           f'<text x="200" y="180" text-anchor="middle" font-size="24">{brand.title()}</text>'
           f'<text x="200" y="350" text-anchor="middle" font-size="18">Illustration: {shape}</text></svg>')
    return "data:image/svg+xml," + quote(svg)


HOUSEHOLD_ITEMS = tuple(dict(item_id=b, name=n, category=c, colours=[colour], shape=s,
    brand_hint=b, purchased_by=p, last_purchased=d, image_url=illustration(b, colour, s),
    display_tag=f"{colour.title()} {s} · {p}") for b,n,c,colour,s,p,d in _ROWS)
