# IMDb Top 250 Movie Tracker

A Python-based automation tool and web dashboard that dynamically scrapes the IMDb Top 250 list using headless Selenium. It features an interactive dashboard to monitor, sort, filter, and extract deep metadata from individual movie pages.

## Features
- **Dynamic Headless Scraping**: Uses Selenium Chrome WebDriver with anti-bot masking to parse JavaScript-rendered content.
- **Micro-Scraping Architecture**: Expandable endpoints to click into individual movies to scrape director, cast, genres, and storyline.
- **Interactive Web Dashboard**: Flask-powered backend serving a modern UI with data-table filtering, search, and decade distribution analytics.
- **Automated Scheduling**: Configured with APScheduler to automatically pull fresh ratings daily.
- **Data Export**: One-click download of the extracted catalog into an Excel-ready CSV for ML and Data Science workflows.

## Prerequisites
- Python 3.8+
- Google Chrome installed on the host machine.

## Installation

1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd "movie tracker"
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the Flask application:
   ```bash
   python app.py
   ```
2. Open your browser and navigate to `http://127.0.0.1:5000`.
3. Click **"Scrape Now"** on the dashboard to populate the local database for the first time.

## Project Structure
- `app.py`: Flask web server, API endpoints, and APScheduler background tasks.
- `scraper.py`: Selenium headless scraping logic.
- `templates/index.html`: The main dashboard UI.
- `static/css/style.css`: Dashboard styling.
- `data/`: Directory where the scraped `imdb_top250.csv` is saved locally (ignored in git).
