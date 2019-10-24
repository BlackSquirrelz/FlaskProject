import scrapy

class LawItem(scrapy.item):
    date = scrapy.Field()
    title = scrapy.Field()
