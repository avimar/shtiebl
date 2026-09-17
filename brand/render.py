"""Render brand/brand.html to the channel/newsletter images.

icon.png   640x640   WhatsApp channel photo, Kit profile/avatar
banner.png 1200x400  Kit email header
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge")
    page = browser.new_page(viewport={"width": 1300, "height": 1200})
    page.goto((HERE / "brand.html").as_uri())
    for name in ["icon", "banner"]:
        out = HERE / f"{name}.png"
        page.locator(f"#{name}").screenshot(path=str(out))
        print("wrote", out)
    browser.close()
