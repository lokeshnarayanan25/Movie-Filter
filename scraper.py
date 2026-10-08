"""
IMDb Top 250 Movie Rating Scraper
==================================
OUTCOME 1 — Reliable Data Extraction:
  Uses Selenium + headless Chrome to handle JavaScript-rendered content
  on IMDb. Without Selenium, the Top 250 list is not accessible via
  simple HTTP requests because it is dynamically loaded.

FEATURE 5 — Expandable:
  scrape_movie_detail(url) scrapes individual movie pages for
  cast, genre, director, and plot — ready to extend further.

Mode: HEADLESS (mandatory)
"""

import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ── Constants ────────────────────────────────────────────────────────
IMDB_TOP250_URL = "https://www.imdb.com/chart/top/"
IMDB_BASE_URL   = "https://www.imdb.com"
OUTPUT_DIR      = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
OUTPUT_FILE     = os.path.join(OUTPUT_DIR, "imdb_top250.csv")


# ═══════════════════════════════════════════════════════════════════
# Driver Factory
# ═══════════════════════════════════════════════════════════════════

def create_driver():
    """
    Create and return a headless Chrome WebDriver.

    OUTCOME 1 — Reliable Data Extraction:
      Headless Chrome renders JavaScript just as a real browser does,
      allowing Selenium to extract fully-loaded dynamic content.
    """
    opts = Options()

    # Headless mode — MANDATORY
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")

    # Anti-bot-detection flags
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=opts)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


# ═══════════════════════════════════════════════════════════════════
# Top 250 List Scraper
# ═══════════════════════════════════════════════════════════════════

def scrape_top250():
    """
    Scrape the IMDb Top 250 Movies list.

    OUTCOME 1 — Uses WebDriverWait to ensure JS-rendered content is
    fully loaded before extraction begins.

    Returns
    -------
    list[dict]
        Each dict: Rank, Title, Year, Rating, IMDb_URL
    """
    driver = create_driver()
    movies = []

    try:
        print("[INFO] Navigating to IMDb Top 250 (JavaScript-rendered page)...")
        driver.get(IMDB_TOP250_URL)

        # Wait for JS to render the movie list
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "li.ipc-metadata-list-summary-item")
            )
        )
        time.sleep(3)  # Allow all lazy-loaded elements to settle

        print("[INFO] Page rendered. Extracting movie data...")

        movie_items = driver.find_elements(
            By.CSS_SELECTOR, "li.ipc-metadata-list-summary-item"
        )
        print(f"[INFO] Found {len(movie_items)} movie items.")

        for index, item in enumerate(movie_items, start=1):
            try:
                # ── Rank ─────────────────────────────────────────
                try:
                    rank_el   = item.find_element(
                        By.CSS_SELECTOR,
                        '[data-testid="title-list-item-ranking"] .ipc-signpost__text'
                    )
                    rank = int(rank_el.text.strip().lstrip("#"))
                except Exception:
                    rank = index

                # ── Title ─────────────────────────────────────────
                try:
                    title = item.find_element(
                        By.CSS_SELECTOR, "h4.ipc-title__text"
                    ).text.strip()
                except Exception:
                    title = item.find_element(
                        By.CSS_SELECTOR, "a.ipc-title-link-wrapper"
                    ).text.strip()

                # ── Year ─────────────────────────────────────────
                try:
                    meta_ul   = item.find_element(
                        By.CSS_SELECTOR, ".cli-title-metadata ul"
                    )
                    year_els  = meta_ul.find_elements(
                        By.CSS_SELECTOR, "li.ipc-inline-list__item"
                    )
                    year = year_els[0].text.strip() if year_els else "N/A"
                except Exception:
                    year = "N/A"

                # ── Rating ───────────────────────────────────────
                try:
                    rating = item.find_element(
                        By.CSS_SELECTOR, "span.ipc-rating-star--rating"
                    ).text.strip()
                except Exception:
                    try:
                        span  = item.find_element(
                            By.CSS_SELECTOR, "span.ipc-rating-star--imdb"
                        )
                        aria  = span.get_attribute("aria-label") or ""
                        rating = aria.split(":")[-1].strip() if ":" in aria else "N/A"
                    except Exception:
                        rating = "N/A"

                # ── IMDb URL (for expandable detail scraping) ────
                try:
                    link_el   = item.find_element(
                        By.CSS_SELECTOR, "a.ipc-title-link-wrapper"
                    )
                    href      = link_el.get_attribute("href") or ""
                    imdb_url  = href.split("?")[0]  # strip ref params
                except Exception:
                    imdb_url = ""

                movies.append({
                    "Rank":     rank,
                    "Title":    title,
                    "Year":     year,
                    "Rating":   rating,
                    "IMDb_URL": imdb_url,
                })

            except Exception as e:
                print(f"[WARN] Skipping item {index}: {e}")
                continue

        print(f"[INFO] Successfully scraped {len(movies)} movies.")

    except Exception as e:
        print(f"[ERROR] Scraping failed: {e}")
        raise

    finally:
        driver.quit()
        print("[INFO] Browser closed.")

    return movies


# ═══════════════════════════════════════════════════════════════════
# FEATURE 5 — Expandable: Individual Movie Detail Scraper
# ═══════════════════════════════════════════════════════════════════

def scrape_movie_detail(imdb_url: str) -> dict:
    """
    FEATURE 5 — Expandable:
    Scrape an individual IMDb movie page for extended details.

    This function is designed to be easily extended — add new
    selectors below to capture additional data (box office,
    awards, trivia, user reviews, etc.).

    Parameters
    ----------
    imdb_url : str
        Full URL of the IMDb title page, e.g.
        "https://www.imdb.com/title/tt0111161/"

    Returns
    -------
    dict
        Keys: genres, director, cast, plot
        Extend this dict to add more fields as needed.
    """
    driver = create_driver()
    detail = {
        "genres":   [],
        "director": "N/A",
        "cast":     [],
        "plot":     "N/A",
    }

    try:
        print(f"[DETAIL] Fetching: {imdb_url}")
        driver.get(imdb_url)

        # Wait for main content block to render
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '[data-testid="title-cast-item__actor"]')
            )
        )
        time.sleep(2)

        # ── Genres ───────────────────────────────────────────────
        # EXTENDABLE: add more chip selectors for sub-genres, themes, etc.
        try:
            chip_els = driver.find_elements(By.CSS_SELECTOR, ".ipc-chip__text")
            detail["genres"] = [
                el.text.strip() for el in chip_els[:5] if el.text.strip()
            ]
        except Exception:
            detail["genres"] = []

        # ── Director ─────────────────────────────────────────────
        # EXTENDABLE: index [1] = writer, [2] = stars section label
        try:
            credit_links = driver.find_elements(
                By.CSS_SELECTOR,
                '[data-testid="title-pc-principal-credit"] a'
            )
            if credit_links:
                detail["director"] = credit_links[0].text.strip()
        except Exception:
            detail["director"] = "N/A"

        # ── Cast (top 5) ──────────────────────────────────────────
        # EXTENDABLE: increase slice or add character names with
        # '[data-testid="title-cast-item__characters"]'
        try:
            cast_els     = driver.find_elements(
                By.CSS_SELECTOR, '[data-testid="title-cast-item__actor"]'
            )
            detail["cast"] = [
                el.text.strip() for el in cast_els[:5] if el.text.strip()
            ]
        except Exception:
            detail["cast"] = []

        # ── Plot ─────────────────────────────────────────────────
        # EXTENDABLE: swap selector for full storyline or user reviews
        try:
            plot_el      = driver.find_element(
                By.CSS_SELECTOR, '[data-testid="plot-xl"]'
            )
            detail["plot"] = plot_el.text.strip()
        except Exception:
            detail["plot"] = "N/A"

        print(f"[DETAIL] Done — genres={detail['genres']}, director={detail['director']}")

    except Exception as e:
        print(f"[DETAIL ERROR] {e}")

    finally:
        driver.quit()

    return detail


# ═══════════════════════════════════════════════════════════════════
# Save & Run
# ═══════════════════════════════════════════════════════════════════

def save_to_csv(movies: list) -> pd.DataFrame:
    """
    Save movie list to CSV.

    OUTCOME 3 — Custom Data Use:
      The exported CSV (utf-8-sig encoded for Excel compatibility)
      can be loaded directly into pandas, scikit-learn pipelines,
      Tableau, Power BI, or any ML/data science workflow.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df = pd.DataFrame(movies)
    # utf-8-sig = BOM-prefixed UTF-8 so Excel opens it correctly
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"[INFO] Data saved to {OUTPUT_FILE}")
    return df


def run_scraper() -> pd.DataFrame:
    """
    Main entry point: scrape Top 250 and save to CSV.

    OUTCOME 2 — Up-to-Date Ratings:
      This function is called by APScheduler daily (configured in
      app.py) to keep ratings current automatically.
    """
    print("=" * 60)
    print("  IMDb Top 250 Movie Rating Scraper")
    print("  Mode : HEADLESS (mandatory)")
    print("  JS   : Handled via Selenium + ChromeDriver")
    print("=" * 60)

    movies = scrape_top250()

    if movies:
        df = save_to_csv(movies)
        print(f"\n[DONE] {len(df)} movies saved to CSV.\n")
        return df

    print("\n[DONE] No movies scraped.\n")
    return pd.DataFrame()


# ── Run directly ─────────────────────────────────────────────────────
if __name__ == "__main__":
    run_scraper()
