import scrapy
from scrapy.utils.response import open_in_browser
from scrapy.selector import Selector

from selenium import webdriver
import time
from scrapy_selenium import SeleniumRequest

class ScrapeDataSpider(scrapy.Spider):
    name = 'scrape_data'

    start_urls = ['https://chrome.google.com/webstore/category/extensions']

    def __init__(self):
        driver = webdriver.Chrome("C:\Program Files (x86)\chromedriver.exe")
        ############ PROVIDE URL AND CATEGORY NAME ########################
        driver.get("https://chrome.google.com/webstore/category/ext/28-photos")
        self.CATEGORY_NAME = "Photos"
        ##################################################################
        time.sleep(5)
        
        scroll_len = 5000
        strike = 0
        old_page_offset = driver.execute_script("return window.pageYOffset")
        while True:
            script = f"window.scrollTo(0, {scroll_len})"
            driver.execute_script(script)
            time.sleep(3)
            scroll_len += 5000

            new_page_offset = driver.execute_script("return window.pageYOffset")
            if old_page_offset == new_page_offset:
                strike += 1
                old_page_offset = new_page_offset
                if strike == 2:
                    break
            else:
                old_page_offset = new_page_offset
                # make strike again zero, so that it always check twice before closing browser
                strike = 0


        self.html = driver.page_source


    def parse(self, response):
        resp = Selector(text=self.html)

        # get all extensions
        all_apps_links = resp.xpath("//div[contains(@class , 'webstore-test-wall-tile')]//a")

        for app_selector in all_apps_links:
            # link of extension
            link = app_selector.xpath("@href").get()
            # image url of extenstion
            img_url = app_selector.xpath("./div[@class='a-P-d ']//div[@class='a-d-Ec']//img/@src").get()
            # icon url of extension
            icon_url = app_selector.xpath("./div[@class='a-P-d ' or @class='a-U-d ']//img[@alt='Extension']/@src").get()
            # ratings and stars od-s-wa
            ratings_reviews = app_selector.xpath(".//div[@class='Y89Uic']//@title").get()
            if ratings_reviews is None:
                ratings_stars = ""
                total_ratings = ""
            else:
                s1_splitted = ratings_reviews.split(' ')
                ratings_stars = s1_splitted[2]
                total_ratings = s1_splitted[7]
            
            # meta_data
            meta = {
                "link": link, 
                "img_url": img_url, 
                "ratings_stars": ratings_stars, 
                "total_ratings": total_ratings,
                "icon_url": icon_url
                }
            # yield request
            yield scrapy.Request(url=link, callback = self.parse_details, meta = meta)


    def parse_details(self, response):
        # - Links
        ext_link = response.meta["link"]
        
        # name
        ext_name = response.xpath("//div[@class='e-f-w-Va']//h1//text()").extract()
        if ext_name:
            ext_name = ext_name[0]
        else:
            ext_name = ""

        # category
        ext_category = response.xpath("//span[@class='e-f-yb-w']//a[@class='e-f-y']//text()").extract()
        # if ext_category is not None:
        #     ext_category = ext_category[0]

        #  Picture
        img_url = response.meta["img_url"]
        if img_url is None:
            img_url = ""

        # Icon
        icon_url = response.meta["icon_url"]
        if icon_url is None:
            icon_url = ""

        # - Rating (stars)
        rating_stars = response.meta['ratings_stars']

        # - Number of ratings
        total_ratings = response.meta['total_ratings']

        # - Description
        ext_desctiption = response.xpath("//pre[@class='C-b-p-j-Oa']//text()").extract()
        if ext_desctiption:
            ext_desctiption = ext_desctiption[0]
        else:
            ext_desctiption = ""


        # - Last update
        ext_last_updated = response.xpath("//span[@class='C-b-p-D-Xe h-C-b-p-D-xh-hh']//text()").extract()
        if ext_last_updated:
            ext_last_updated = ext_last_updated[0]
        else:
            ext_last_updated = ""

        yield {
            'name' : ext_name,
            'category': self.CATEGORY_NAME,
            'link': ext_link,
            'img_url': img_url,
            'icon_url': icon_url,
            'ratings(stars)': rating_stars,
            'number of ratings': total_ratings,
            'description': ext_desctiption,
            'last_updated': ext_last_updated
        }
