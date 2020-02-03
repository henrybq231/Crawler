import scrapy
import json
import string
import codecs
from scrapy.settings import Settings
from scrapy.crawler import CrawlerProcess
from scrapy.item import Item, Field
from scrapy.settings.default_settings import FEED_EXPORT_ENCODING, FEED_EXPORTERS, FEED_FORMAT, FEED_URI
import datetime


class TextCleaningPipeline(object):

    def process_item(self, item, spider):
        item['text'] = self._clean_text(item['text'])
        return item


class JsonWithEncodingPipeline(object):
    def open_spider(self, spider):
        self.file = codecs.open('data.json', 'w', encoding='utf-8')
        # self.file = open(spider.settings['JSON_FILE'], 'w', encoding='utf-8')

    def process_item(self, item, spider):
        line = json.dumps(
            dict(item),
            sort_keys=True,
            indent=4,
            separators=(',', ': '),
            ensure_ascii=False
        ) + ", \n"
        self.file.write(line)
        return item

    def spider_closed(self, spider):
        self.file.close()



class GeneralInfo(Item):
    url = Field()
    title = Field()
    snipet = Field()
    timestamp = Field()

class DetailInfo(Item):
    url = Field()
    content = Field()



class CrawlerGeneral(scrapy.Spider):

    #name of spider
    name = 'general'

    custom_settings = {
        FEED_URI: 'spider1_' + datetime.datetime.today().strftime('%y%m%d') + '.json',
        FEED_FORMAT: 'json',
        FEED_EXPORTERS: {
            'json': 'scrapy.exporters.JsonItemExporter',
        },
        FEED_EXPORT_ENCODING: 'utf-8',
    }

    #list of url
    url = []

    for num in range(1, 2):
        url.append('http://cafef.vn/doc-nhanh/trang-%s.chn' % num)

    start_urls = url

    #delay crawling the following article
    download_delay = 1.5

    # get url
    def parse(self, response):

        for url in response.css('div.nv-text-cont'):
            general_info = GeneralInfo()
            general_info['url'] = 'http://cafef.vn/' + url.css('a::attr(href)').get()
            general_info['title'] = url.css('a::text').get()

            nextReq = 'http://cafef.vn' + url.css('a::attr(href)').get()
            meta = {}
            meta['general_info'] = general_info
            yield scrapy.Request(url = nextReq, callback=self.more_conten, meta=meta)

    def more_conten(self, response):
        response.meta['general_info']['snipet'] = response.css('.sapo::text').get().lstrip().rstrip()
        response.meta['general_info']['timestamp'] = response.css('.pdate::text').get()
        yield response.meta['general_info']


class CrawlerContent(scrapy.Spider):
    name = 'content'

    # list of url
    url = []

    for num in range(1, 2):
        url.append('http://cafef.vn/doc-nhanh/trang-%s.chn' % num)

    start_urls = url

    #delay crawling the following article
    download_delay = 1.5

    def parse(self, response):
        detail_info = DetailInfo()
        for url in response.css('div.nv-text-cont'):
            detail_info['url'] = 'http://cafef.vn/' + url.css('a::attr(href)').get()
            nextReq = 'http://cafef.vn' + url.css('a::attr(href)').get()
            meta = {}
            meta['detail_info'] = detail_info
            yield scrapy.Request(url=nextReq, callback=self.parse_cafef, meta=meta)

    #crawl
    def parse_cafef(self, response):

        #crawl content
        for content in response.xpath('//*[@id="mainContent"]'):
            arr = content.xpath('.//p/text()').getall()
            # str = '\\n '.join(arr)
            response.meta['detail_info']['content'] = arr

        yield response.meta['detail_info']






    # def parse(self, response):
    #     article = DetailInfo()
    #
    #     for url in response.xpath('//*[@id="mainContent"]'):
    #         article['content'] = content.xpath('.//p/text()').getall()
    #
    #     yield article


settings = Settings()
settings.set('ITEM_PIPELINES', {
    '__main__.TextCleaningPipeline': 700
}, priority='cmdline'
             )

settings.set('ITEM_PIPELINES', {
    '__main__.JsonWithEncodingPipeline': 701
}, priority='cmdline'
             )

crawler = CrawlerProcess(settings)

# spider = CrawlerGeneral()

# crawler.configure()
crawler.crawl(CrawlerGeneral)
crawler.crawl(CrawlerContent)
crawler.start()