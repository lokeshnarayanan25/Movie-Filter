"""Inspect a single IMDb movie detail page for correct selectors."""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--disable-gpu")
opts.add_argument("--window-size=1920,1080")
opts.add_argument("--disable-blink-features=AutomationControlled")
opts.add_experimental_option("excludeSwitches", ["enable-automation"])
opts.add_experimental_option("useAutomationExtension", False)
opts.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

# Shawshank Redemption detail page
driver.get("https://www.imdb.com/title/tt0111161/")
time.sleep(5)

selectors = {
    "genres": '[data-testid="genres"] a span',
    "genres2": '.ipc-chip__text',
    "director": '[data-testid="title-pc-principal-credit"] a',
    "cast_items": '[data-testid="title-cast-item__actor"]',
    "plot_xl": '[data-testid="plot-xl"]',
    "plot_xs": 'span[data-testid="plot-xs_to_m"]',
    "plot_l": '[data-testid="plot-l"]',
    "storyline": '[data-testid="storyline-plot-summary"]',
}

for name, sel in selectors.items():
    els = driver.find_elements(By.CSS_SELECTOR, sel)
    texts = [e.text.strip() for e in els[:5] if e.text.strip()]
    print(f"[{name}] ({len(els)} els): {texts}")

driver.quit()
