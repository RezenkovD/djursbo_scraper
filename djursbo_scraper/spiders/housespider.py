import asyncio
import re

import scrapy
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
from scrapy_playwright.page import PageMethod

from djursbo_scraper.items import DjursboScraperItem


class HousespiderSpider(scrapy.Spider):
    name = "housespider"
    allowed_domains = ["djursbo.dk"]

    def start_requests(self):
        url = "https://djursbo.dk/for-boligsoegende/afdeling/"
        yield scrapy.Request(
            url,
            meta=dict(
                playwright=True,
                playwright_include_page=True,
            ),
        )

    async def parse(self, response):
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            page = await browser.new_page()
            await page.goto(response.url)
            # cookie
            button_selector = "button.btn"
            try:
                button = page.locator(button_selector).get_by_text(" Accepter alle ")
                await button.click()
                await asyncio.sleep(10)
            except PlaywrightTimeoutError:
                pass

            while True:
                # get page
                page_content = await page.content()
                # use Scrapy for parsing
                scrapy_selector = scrapy.Selector(text=page_content)
                div_elements = scrapy_selector.css("div.result")
                for div in div_elements:
                    new_source = (
                        "https://djursbo.dk/" + div.css("a.link::attr(href)").get()
                    )
                    yield scrapy.Request(
                        new_source,
                        meta=dict(
                            playwright=True,
                            playwright_include_page=True,
                        ),
                        callback=self.parse_page,
                    )
                # click button
                button_selector = "a.active-shadow"
                try:
                    button = page.locator(button_selector).get_by_text("Næste").nth(1)
                    await button.click()
                except PlaywrightTimeoutError:
                    break
            await browser.close()

    async def parse_page(self, response):
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            page = await browser.new_page()
            await page.goto(response.url)
            # cookie
            button_selector = "button.btn"
            try:
                button = page.locator(button_selector).get_by_text(" Accepter alle ")
                await button.click()
                await asyncio.sleep(10)
            except PlaywrightTimeoutError:
                pass
            # get page
            page_content = await page.content()
            # use Scrapy for parsing
            scrapy_selector = scrapy.Selector(text=page_content)
            div_elements = scrapy_selector.css("div.content-adjusment")
            title = div_elements.css("h1::text").get()
            cleaned_title = re.sub(r"\s+", " ", title).strip()
            addres = div_elements.css(
                "div.department-addresses span.ng-scope span.ng-binding::text"
            ).getall()
            if addres is None:
                addres = []
            str_addres = ", ".join(addres)
            joined_addresses = re.sub(r",\s*-\s*,", " - ", str_addres)
            cleaned_addresses = re.sub(r"\s*([,-])\s*", r"\1", joined_addresses)
            house_item = DjursboScraperItem()
            house_item["title"] = cleaned_title
            house_item["description"] = div_elements.css(
                "div.department-description::text"
            ).get()
            house_item["price"] = div_elements.css("span.larger.ng-binding::text").get()
            house_item["address"] = cleaned_addresses
            yield house_item
