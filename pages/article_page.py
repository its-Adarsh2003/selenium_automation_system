from typing import Tuple, Optional, List
from selenium.webdriver.common.by import By
from utils.logger import log


class ArticlePage:
    def __init__(self, driver):
        self.driver = driver

    def read_article(self, url: str) -> Tuple[str, str, Optional[str]]:
        log(f"Opening article page: {url}")
        self.driver.get(url)

        # Title
        title_el = self.driver.find_element(By.TAG_NAME, "h1")
        title_es = title_el.text.strip()

        # Content
        paragraphs = self.driver.find_elements(By.TAG_NAME, "p")
        content_parts = [p.text.strip() for p in paragraphs if p.text.strip()]
        content_es = " ".join(content_parts)

        image_url: Optional[str] = None

        # 1) Try article-scoped images first
        article_img_selectors: List[str] = [
            "article picture img",
            "article figure img",
            "article img",
        ]

        def pick_first_valid_img(selectors: List[str]) -> Optional[str]:
            for selector in selectors:
                try:
                    elems = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for img in elems:
                        src = img.get_attribute("src") or img.get_attribute("data-src")
                        if src and not src.startswith("data:image"):
                            return src
                except Exception:
                    continue
            return None

        image_url = pick_first_valid_img(article_img_selectors)

        if not image_url:
            fallback_selectors: List[str] = [
                "main img",
                "header img",
                "img",
            ]
            image_url = pick_first_valid_img(fallback_selectors)

        log(f"Extracted article; image_url={image_url}")
        return title_es, content_es, image_url
