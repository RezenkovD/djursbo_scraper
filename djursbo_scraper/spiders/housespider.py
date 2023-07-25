import asyncio
import scrapy
from playwright.sync_api import sync_playwright
from scrapy_playwright.page import PageMethod
from playwright.async_api import async_playwright


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
            button = page.locator(button_selector).get_by_text(" Accepter alle ")
            await button.click()
            await asyncio.sleep(10)

            while True:
                # get page
                page_content = await page.content()
                # use Scrapy for parsing
                scrapy_selector = scrapy.Selector(text=page_content)
                div_elements = scrapy_selector.css("div.result")
                for div in div_elements:
                    yield {
                        "Title": div.css("h3.ng-binding::text").get(),
                        "Street": div.css("li.ng-binding::text").getall(),
                    }
                # click button
                button_selector = "a.active-shadow"
                button = page.locator(button_selector).get_by_text("Næste").nth(1)
                if not button:
                    break
                await button.click()
            await browser.close()
