# -*- coding:utf-8 -*-
from scrapy.crawler import CrawlerProcess
from scrapy.conf import settings
from spiders.emis_spider import EmisSpider

# mongo_uri = '127.0.0.1:27017'
# connection = pymongo.MongoClient(mongo_uri)
# connection.fcenter.authenticate("fcenter", "123456")
# db = connection.fcenter

# collection_name = 'alumn_home'
# for item in db[collection_name].find( {'sourceId': {'$exists': False}, 'crawl': {'$exists': False}},{"_id": 1, 'image': 1}):
#    print item
process = CrawlerProcess(settings)
process.crawl(EmisSpider)
process.start()  # the script will block here until all crawling jobs are finished
