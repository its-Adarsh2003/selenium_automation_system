import os
import sys
import ast
import pandas as pd
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from utils.driver_setup import get_local_driver
from pages.home_page import HomePage
from pages.opinion_page import OpinionPage
from pages.article_page import ArticlePage

from utils.translation_api import translate_to_english
from utils.text_analysis import analyze_words, find_repeated_words_in_titles
from utils.logger import log
from utils.notifications import notify_failure
from utils.images_downloader import download_images_parallel
from config import ARTICLE_LIMIT, RESULT_FILE, USE_PARALLEL, MAX_WORKERS, FORCE_FAILURE 

downloaded_image_urls = set()
download_lock = Lock()


def save_results(rows):
    reports_dir = os.path.dirname(RESULT_FILE)
    if reports_dir and not os.path.exists(reports_dir):
        os.makedirs(reports_dir, exist_ok=True)

    df = pd.DataFrame(rows)

    if os.path.exists(RESULT_FILE):
        df.to_csv(RESULT_FILE, mode="a", header=False, index=False)
    else:
        df.to_csv(RESULT_FILE, index=False)


def process_with_own_driver(article_meta):
    driver = get_local_driver()
    try:
        article_page = ArticlePage(driver)
        url = article_meta["url"]

        log(f"Reading article (own driver): {url}")
        title_es, content_es, image_url = article_page.read_article(url)

        title_en = translate_to_english(title_es)
        word_counts = analyze_words(content_es)

        downloaded_paths = []
        if image_url:
            with download_lock:
                if image_url not in downloaded_image_urls:
                    downloaded_paths = download_images_parallel([image_url])
                    downloaded_paths = [p for p in downloaded_paths if p is not None]
                    if downloaded_paths:
                        downloaded_image_urls.add(image_url)
                        log(f"Image downloaded for URL: {image_url}")
                else:
                    log(f"Image already downloaded, skipping duplicate: {image_url}")

        return {
            "article_url": url,
            "title_es": title_es,
            "title_en": title_en,
            "word_counts_list": str(word_counts),
            "image_url": image_url,
            "image_paths": str(downloaded_paths),
        }
    except Exception as e:
        log(f"ERROR processing article: {str(e)}")
        return None
    finally:
        driver.quit()


def run_pipeline():
    if FORCE_FAILURE:
        msg = "Forced failure triggered from config.FORCE_FAILURE"
        log(msg)
        notify_failure(msg)
        raise RuntimeError(msg)
    
    driver = get_local_driver()

    home = HomePage(driver)
    opinion = OpinionPage(driver)

    log("Open homepage")
    home.open()
    home.accept_cookies()
    home.go_to_opinion()

    log(f"Scraping first {ARTICLE_LIMIT} opinion articles")
    articles_meta = opinion.get_first_articles(ARTICLE_LIMIT)

    rows = []

    if USE_PARALLEL:
        # Parallel: per-article own driver
        log(f"Processing articles in PARALLEL with max_workers={MAX_WORKERS}")
        driver.quit()

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [
                executor.submit(process_with_own_driver, meta)
                for meta in articles_meta
            ]
            for f in as_completed(futures):
                try:
                    result = f.result()
                    if result is not None:
                        rows.append(result)
                except Exception as e:
                    log(f"ERROR in parallel task: {str(e)}")
    else:
        log("Processing articles SEQUENTIALLY with single shared driver")
        article_page = ArticlePage(driver)

        for meta in articles_meta:
            url = meta["url"]
            log(f"Reading article (single driver): {url}")
            try:
                title_es, content_es, image_url = article_page.read_article(url)
                title_en = translate_to_english(title_es)
                word_counts = analyze_words(content_es)

                downloaded_paths = []
                if image_url:
                    if image_url not in downloaded_image_urls:
                        downloaded_paths = download_images_parallel([image_url])
                        downloaded_paths = [
                            p for p in downloaded_paths if p is not None
                        ]
                        if downloaded_paths:
                            downloaded_image_urls.add(image_url)
                            log(f"Image downloaded for URL: {image_url}")
                    else:
                        log(f"Image already downloaded, skipping duplicate: {image_url}")

                rows.append({
                    "article_url": url,
                    "title_es": title_es,
                    "title_en": title_en,
                    "word_counts_list": str(word_counts),
                    "image_url": image_url,
                    "image_paths": str(downloaded_paths),
                })
            except Exception as e:
                log(f"ERROR processing article in single-thread mode: {str(e)}")

        driver.quit()

    save_results(rows)
    log(f"Pipeline completed successfully - {len(rows)} articles processed")

    print("\n================ EL PAÍS OPINION SCRAPE REPORT ================")
    print(f"Total articles processed: {len(rows)}")

    print("\n-- Article titles (EN) --")
    for idx, r in enumerate(rows, start=1):
        print(f"{idx}. {r.get('title_en') or '[no title]'}")

    titles_en = [r["title_en"] for r in rows if r.get("title_en")]
    if titles_en:
        repeated = find_repeated_words_in_titles(titles_en, min_count=3)
        print("\n-- Repeated words in titles (min_count=3) --")
        print(repeated)
    else:
        print("\n-- Repeated words in titles --")
        print("No titles available for analysis.")

    all_counts = Counter()
    for r in rows:
        wc_str = r.get("word_counts_list")
        if not wc_str:
            continue
        try:
            wc = dict(ast.literal_eval(wc_str))
            all_counts.update(wc)
        except Exception:
            continue

    if all_counts:
        top_words = all_counts.most_common(15)
        print("\n-- Top 15 words across article bodies --")
        for word, count in top_words:
            print(f"{word}: {count}")
    else:
        print("\n-- Top words across article bodies --")
        print("No body word frequency data available.")

    print("===============================================================\n")


if __name__ == "__main__":
    run_pipeline()
