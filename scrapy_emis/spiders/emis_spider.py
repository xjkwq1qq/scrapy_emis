# -*- coding:utf-8 -*-
import scrapy
import re

from scrapy_redis.spiders import RedisSpider
from urlparse import urljoin
import json

# redis-cli
# lpush scrapy_emis:start_urls http://www.tax.sh.gov.cn/pub/xxgk/zcfg/
# 删除队列
# del "shanghaiTaxSpider:dupefilter"
# del "shanghaiTaxSpider:requests"
class EmisSpider(RedisSpider):
    custom_settings = {
        'ITEM_PIPELINES': {
            'scrapy_emis.pipelines.ScrapyEmisPipeline': 1,
        }
    }
    """Spider that reads urls from redis queue (myspider:start_urls)."""
    name = 'scrapy_emis'
    redis_key = 'scrapy_emis:start_urls'

    def __init__(self, *args, **kwargs):
        # Dynamically define the allowed domains list.
        domain = kwargs.pop('domain', '')
        self.allowed_domains = filter(None, domain.split(','))
        super(EmisSpider, self).__init__(*args, **kwargs)

    # 获取分类列表
    def parse(self, response):
        for item in response.css('#acc1 > li > div > div  a.get_custom_tables'):
            for href in item.xpath('@href').extract():
                # print item.html()
                # print urljoin('https://www.emis.com/php/industries/companies', href)+'&pc=ZZ&subp=&sort=&indut=main&keyword='
                yield scrapy.Request(
                    urljoin('https://www.emis.com/php/industries/companies',href) + '&pc=ZZ&subp=&sort=&indut=main&keyword=',
                    callback=self.get_page_list_parse, dont_filter=True)



    # 读取分页数据
    def get_page_list_parse(self, response):
        # 抓取公司地址
        for item in response.css('#content > div > div > ul > li'):
            for companyUrl in item.xpath('a/@href').extract():
                yield scrapy.Request(urljoin('https://www.emis.com/',companyUrl), callback=self.get_comany_page,dont_filter=False)
        # 翻页
        pageNum = self.get_pageNum_fromUrl(response.url)
        for item in response.css('#content > div > div > div.grey-bottom.p-1-05em.clearfix > div > span > a'):
            for page in  item.xpath('text()').extract():
                if(int(page) == (int(pageNum)+1)):
                    for href in item.xpath('@href').extract():
                        yield scrapy.Request(urljoin('https://www.emis.com/php/industries/companies',href), callback=self.get_page_list_parse,dont_filter=False)

    # 公司信息解析
    def get_comany_page(self, response):
        # pass
        data = json.loads(response.body)
        print data.get('url')
        print data.get('activities')
        pass

    def get_pageNum_fromUrl(self,url):
        values = url.split('?')[- 1 ]
        for key_value in values.split('&'):
            key_value_a = key_value.split('=')
            if('page' == key_value_a[0]):
                return key_value_a[1]
        return 1

if __name__ == "__main__":
    # print(CninfoSpider.ndbg_year(u"摩根太平洋：摩根太平洋证券基金年度报告（2017年9月30日）"))
    # print(ShanghaiTaxSpider.parse_classification(u"上海市财政局 上海市地方税务局"))
    # print(ShanghaiTaxSpider.parse_classification(u"国家税务总局"))
    pass
