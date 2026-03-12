from selenium.webdriver.common.by import By


class OpinionPage:
    def __init__(self, driver):
        self.driver = driver

    def get_first_articles(self, n=5):
        articles = self.driver.find_elements(By.CSS_SELECTOR, "article")

        results = []
        for article in articles[:n]:
            link = article.find_element(By.TAG_NAME, "a").get_attribute("href")
            title = article.text
            results.append({
                "title": title,
                "url": link,
            })

        return results
