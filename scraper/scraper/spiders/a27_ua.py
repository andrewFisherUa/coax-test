# -*- coding: utf-8 -*-
import scrapy
import re


class Tile(scrapy.Item):
    name = scrapy.Field()
    height = scrapy.Field()
    width = scrapy.Field()


class A27UaSpider(scrapy.Spider):
    name = 'a27_ua'
    allowed_domains = ['27.ua']
    start_urls = ['https://27.ua/ua/shop/keramicheskaya-plitka-i-keramogranit/fs/otdelochnaya-poverhnost-stena/']
    base = 'https://27.ua{}'
    counter = 0

    def parse(self, response):
        next_page = response.xpath('//a[@rel="next"]/@href').extract()
        next_page = self.base.format(next_page[0]) if next_page else None
        # if next_page:
        self.counter += 1
        if self.counter < 2:
            yield from self.parse_tiles(response)
            yield scrapy.Request(next_page, callback=self.parse, 
                                 dont_filter=True)

    def parse_tiles(self, response):
        tiles = response.xpath('//b[@class="nc"]/text()').extract()
        for tile in tiles:
            ser = re.search(r'(?P<height>\d+,*?\d*?)[\*xх]+(?P<width>\d+,*?\d*?)', tile)
            if not ser:
                continue
            height = ser.group('height')
            width = ser.group('width')
            height = float(height.replace(',', '.')) * 10 if height else None
            width = float(width.replace(',', '.')) * 10 if width else None
            if height and width:
                yield Tile(height=height, width=width, name=tile.strip())
