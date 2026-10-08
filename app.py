
import io
import os
import datetime
import atexit
import threading
import pandas as pd
from flask import Flask, render_template, jsonify, request, Response

from scraper import run_scraper, scrape_movie_detail, OUTPUT_FILE

app = Flask(__name__)

scrape_status = {
    "is_running": False,
    "error": None,
    "last_count": 0
}

from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler(daemon=True)
SCHEDULE_HOUR   = 2   # 2:00 AM daily by default
SCHEDULE_MINUTE = 0
SCHEDULER_JOB_ID = "daily_imdb_scrape"

def _scheduled_job():
    """Job function executed by APScheduler on the daily trigger."""
    print(f"[SCHEDULER] Auto-scrape started at {datetime.datetime.now()}")
    scrape_status["is_running"] = True
    scrape_status["error"] = None
    try:
        df = run_scraper()
        scrape_status["last_count"] = len(df)
        print("[SCHEDULER] Auto-scrape completed successfully.")
    except Exception as e:
        scrape_status["error"] = str(e)
        print(f"[SCHEDULER] Auto-scrape failed: {e}")
    finally:
        scrape_status["is_running"] = False

def _start_scheduler():
    """Start the background scheduler (only in the main process)."""
    scheduler.add_job(
        func=_scheduled_job,
        trigger="cron",
        hour=SCHEDULE_HOUR,
        minute=SCHEDULE_MINUTE,
        id=SCHEDULER_JOB_ID,
        replace_existing=True,
    )
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown(wait=False))
    print(f"[SCHEDULER] Started — daily scrape at {SCHEDULE_HOUR:02d}:{SCHEDULE_MINUTE:02d}")

if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not os.environ.get("FLASK_DEBUG"):
    _start_scheduler()



def load_data() -> pd.DataFrame:
    """Load scraped CSV. Returns empty DF if not yet scraped."""
    if os.path.exists(OUTPUT_FILE):
        return pd.read_csv(OUTPUT_FILE)
    return pd.DataFrame(columns=["Rank", "Title", "Year", "Rating", "IMDb_URL"])


def _next_run_str() -> str:
    job = scheduler.get_job(SCHEDULER_JOB_ID)
    if job and job.next_run_time:
        return job.next_run_time.strftime("%d %b %Y, %I:%M %p")
    return "N/A"

#───────Routes──────────────────────

@app.route("/")
def index():
    """Main dashboard page."""
    df = load_data()
    movies = df.to_dict(orient="records")
    total = len(movies)

    last_updated = ""
    if os.path.exists(OUTPUT_FILE):
        ts = os.path.getmtime(OUTPUT_FILE)
        last_updated = datetime.datetime.fromtimestamp(ts).strftime("%d %b %Y, %I:%M %p")

    if total > 0:
        df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")
        df["Year"]   = pd.to_numeric(df["Year"],   errors="coerce")
        avg_rating   = round(df["Rating"].mean(), 2)
        highest = df.loc[df["Rating"].idxmax()].to_dict() if not df["Rating"].isna().all() else {}
        lowest  = df.loc[df["Rating"].idxmin()].to_dict() if not df["Rating"].isna().all() else {}
        df["Decade"] = (df["Year"] // 10 * 10).astype("Int64")
        decade_counts = {str(k): v for k, v in df.groupby("Decade").size().items()}
    else:
        avg_rating    = 0
        highest       = {}
        lowest        = {}
        decade_counts = {}

    return render_template(
        "index.html",
        movies=movies,
        total=total,
        avg_rating=avg_rating,
        highest=highest,
        lowest=lowest,
        decade_counts=decade_counts,
        last_updated=last_updated,
        next_run=_next_run_str(),
        schedule_hour=SCHEDULE_HOUR,
        schedule_minute=SCHEDULE_MINUTE,
    )


# ── Scrape ──────────────────────────────────────────────────────────

@app.route("/api/scrape", methods=["POST"])
def trigger_scrape():
    """Manually trigger a full Top 250 scrape in the background."""
    if scrape_status["is_running"]:
        return jsonify({"status": "running", "message": "Scrape is already in progress."})

    def run_in_background():
        scrape_status["is_running"] = True
        scrape_status["error"] = None
        try:
            df = run_scraper()
            scrape_status["last_count"] = len(df)
        except Exception as e:
            scrape_status["error"] = str(e)
        finally:
            scrape_status["is_running"] = False

    thread = threading.Thread(target=run_in_background)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "status":  "started",
        "message": "Scraping started in the background."
    })

@app.route("/api/scrape/status")
def get_scrape_status():
    """Return the current status of the background scraper."""
    return jsonify(scrape_status)

# ── FEATURE 5: Individual Movie Detail ──────────────────────────────

@app.route("/api/movie-detail")
def movie_detail():
    """
    FEATURE 5 — Expandable:
    Scrape an individual IMDb movie page on demand.
    Query param: ?url=https://www.imdb.com/title/tt0111161/
    Returns: { genres, director, cast, plot }

    Easily extendable — add new fields to scrape_movie_detail()
    in scraper.py without changing this endpoint.
    """
    url = request.args.get("url", "").strip()
    if not url or "imdb.com" not in url:
        return jsonify({"error": "Invalid or missing IMDb URL."}), 400
    try:
        detail = scrape_movie_detail(url)
        return jsonify(detail)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Schedule Control ─────────────────────────────────────────────────

@app.route("/api/schedule/status")
def schedule_status():
    """Return current scheduler status."""
    job = scheduler.get_job(SCHEDULER_JOB_ID)
    return jsonify({
        "active":      job is not None,
        "next_run":    _next_run_str(),
        "hour":        SCHEDULE_HOUR,
        "minute":      SCHEDULE_MINUTE,
    })


@app.route("/api/schedule/run-now", methods=["POST"])
def schedule_run_now():
    """Trigger the scheduled job immediately (same as /api/scrape)."""
    try:
        scheduler.add_job(
            func=_scheduled_job,
            trigger="date",
            run_date=datetime.datetime.now() + datetime.timedelta(seconds=1),
            id="manual_trigger",
            replace_existing=True,
        )
        return jsonify({"status": "success", "message": "Scrape triggered via scheduler."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ── Data APIs ────────────────────────────────────────────────────────

@app.route("/api/movies")
def api_movies():
    """JSON movie list. Supports ?q= search."""
    df = load_data()
    q  = request.args.get("q", "").strip().lower()
    if q:
        df = df[df["Title"].str.lower().str.contains(q, na=False)]
    return jsonify(df.to_dict(orient="records"))


@app.route("/api/stats")
def api_stats():
    """Summary statistics as JSON."""
    df = load_data()
    if df.empty:
        return jsonify({"total": 0})
    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")
    df["Year"]   = pd.to_numeric(df["Year"],   errors="coerce")
    return jsonify({
        "total":        len(df),
        "avg_rating":   round(df["Rating"].mean(), 2),
        "max_rating":   round(df["Rating"].max(), 2),
        "min_rating":   round(df["Rating"].min(), 2),
        "newest_year":  int(df["Year"].max()),
        "oldest_year":  int(df["Year"].min()),
    })


# ── OUTCOME 3: CSV Download ──────────────────────────────────────────

@app.route("/download/csv")
def download_csv():
    """
    OUTCOME 3 — Custom Data Use:
    Download the scraped IMDb Top 250 data as a CSV file.
    The file is utf-8-sig encoded (Excel-compatible) and ready
    for use in pandas, scikit-learn, Tableau, Power BI, etc.
    """
    df = load_data()
    if df.empty:
        return Response("No data available. Please scrape first.",
                        status=404, mimetype="text/plain")
    output = io.StringIO()
    df.to_csv(output, index=False, encoding="utf-8")
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=imdb_top250.csv"},
    )


# ── Entry Point ──────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n[*] IMDb Top 250 Dashboard")
    print("    Open http://127.0.0.1:5000 in your browser\n")
    app.run(debug=True, port=5000)
