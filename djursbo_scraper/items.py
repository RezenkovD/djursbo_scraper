# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class DjursboScraperItem(scrapy.Item):
    title = scrapy.Field()
    description = scrapy.Field()
    price = scrapy.Field()
    address = scrapy.Field()
