"""Debug script to inspect IMDb page structure."""
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
driver.get("https://www.imdb.com/chart/top/")
time.sleep(8)

src = driver.page_source
print("Page title:", driver.title)
print("Page length:", len(src))

# Check for common selectors
selectors = [
    "li.ipc-metadata-list-summary-item",
    "div.ipc-metadata-list-summary-item__tc",
    "h3.ipc-title__text",
    "a.ipc-title-link-wrapper",
    '[data-testid="title-metadata-item"]',
    "td.titleColumn",
    ".cli-children",
]
for sel in selectors:
    els = driver.find_elements(By.CSS_SELECTOR, sel)
    print(f"  [{sel}] => {len(els)} elements")

# Save page source for inspection
with open("data/page_source.html", "w", encoding="utf-8") as f:
    f.write(src)
print("\nPage source saved to data/page_source.html")

driver.quit()
