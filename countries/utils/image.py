import os
from PIL import Image, ImageDraw, ImageFont


CACHE_DIR = os.path.join(os.getcwd(), 'cache')


if not os.path.exists(CACHE_DIR):
   os.makedirs(CACHE_DIR, exist_ok=True)


def generate_summary_image(total, top_countries, timestamp):
    width, height = 1200, 800
    img = Image.new('RGB', (width, height), color='white')
    d = ImageDraw.Draw(img)


    try:
        font_title = ImageFont.truetype('DejaVuSans-Bold.ttf', 40)
        font_text = ImageFont.truetype('DejaVuSans.ttf', 20)
    except Exception:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()


    d.text((40, 40), 'Country Cache Summary', font=font_title, fill=(0,0,0))
    d.text((40, 110), f'Total countries: {total}', font=font_text, fill=(0,0,0))
    d.text((40, 140), f'Last refreshed at: {timestamp}', font=font_text, fill=(0,0,0))


    d.text((40, 190), 'Top 5 by estimated GDP', font=font_text, fill=(0,0,0))
    y = 230
    for i, c in enumerate(top_countries):
        line = f"{i+1}. {c['name']} — {c['estimated_gdp']:, .2f}"
        d.text((60, y), line, font=font_text, fill=(0,0,0))
        y += 36


    out_path = os.path.join(CACHE_DIR, 'summary.png')
    img.save(out_path)
    return out_path
