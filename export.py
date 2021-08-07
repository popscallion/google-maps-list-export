import pickle
import re
import time

from selenium.webdriver import Firefox
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options


def main():
    print("Starting driver")
    options = Options()
    options.headless = True

    driver = Firefox(options=options)
    driver.implicitly_wait(5)
    driver.get("https://www.google.com")

    with open("cookies.pkl", "rb") as f:
        cookies = pickle.load(f)
    for cookie in cookies:
        driver.add_cookie(cookie)

    print("Going to Maps")
    driver.get("")
    time.sleep(1)

    print("Scrolling down")
    previous_page = None
    scrollbox = driver.find_element_by_class_name("section-scrollbox")
    while previous_page is None or previous_page != driver.page_source:
        previous_page = driver.page_source
        scrollbox.send_keys(Keys.PAGE_DOWN * 5)
        time.sleep(1)

    print("Scraping entries")
    entries = []
    item_count = len(driver.find_elements_by_xpath("//div[contains(@class,'section-scrollbox')]/div")) // 2
    for i in range(item_count):
        item = driver.find_elements_by_xpath("//div[contains(@class,'section-scrollbox')]/div")[i * 2].click()

        time.sleep(1)
        url = driver.current_url

        coords = re.findall(r"(-?\d+\.\d+)!4d(-?\d+\.\d+)", url)[0]
        name = driver.find_element_by_tag_name("h1").text
        print(f"Found {name} at {', '.join(coords)}")

        driver.find_element_by_class_name("omnibox-pane-container").click()
        time.sleep(1)

        entries.append({"name": name, "coords": coords})

    driver.close()


if __name__ == '__main__':
    main()
