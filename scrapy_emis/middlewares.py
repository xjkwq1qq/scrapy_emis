# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait  # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC  # available since 2.26.0
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from scrapy.http import HtmlResponse
import re
import os
import json
import shutil
from time import sleep
import urlparse
from selenium.common.exceptions import NoSuchWindowException, WebDriverException, TimeoutException
import traceback


class ScrapyEmisSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class ScrapyEmisDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.
    browser = None
    timeout = 20
    rootPath = 'C:\work\data\emis'
    downloadPath = os.path.join(rootPath, 'downlad')

    def __init__(self):

        # 不存在则创建
        if not os.path.isdir(self.downloadPath):
            os.makedirs(self.downloadPath)
        # 设置下载路径
        options = webdriver.ChromeOptions()
        prefs = {'profile.default_content_settings.popups': 0, 'download.default_directory': self.downloadPath}
        options.add_experimental_option('prefs', prefs)

        if self.browser:
            self.__del__()

        self.browser = webdriver.Chrome(
            executable_path=os.path.abspath(os.path.dirname(os.getcwd())) + '\scrapy_emis\\bin\chromedriver.exe',
            chrome_options=options)

    def __del__(self):
        try:
            self.browser.quit()
        except Exception:
            pass

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):

        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        # 获取行业列表页面
        # self.browser = webdriver.Ie(executable_path=os.path.abspath(os.path.dirname(os.getcwd())) + '\scrapy_emis\\bin\IEDriverServer.exe')
        # self.browser = webdriver.Chrome(executable_path=os.path.abspath(os.path.dirname(os.getcwd())) + '\scrapy_emis\\bin\chromedriver.exe')

        if re.match(r"https://intellinet.deloitte.com/Secure.*", request.url, re.M | re.I):
            return self.getIndustries(request, spider)
            # return HtmlResponse(url=request.url, status=500, request=request)
        # 获取公司列表页面
        elif re.match(r"https://www.emis.com/php/industries/companies.*", request.url, re.M | re.I):
            return self.getCompanies(request, spider)

        # 获取公司信息并下载附件
        elif re.match(r"https://www.emis.com/php/companies.*", request.url, re.M | re.I):
            return self.getCompanyExcel(request, spider)
        else:
            return HtmlResponse(url=request.url, status=500, request=request)

    # 获取行业列表页面
    def getIndustries(self, request, spider):
        url = "https://www.emis.com/php/industries/companies?&pc=CN&prod[]=CN&indu=721&change_selected_countries=1"
        waits = []
        waits.append(EC.title_contains("EMISPRO - Industries - Companies List"))
        waits.append(EC.presence_of_element_located((By.CSS_SELECTOR, '#acc1 > li:nth-child(4) > h4')))
        return self.getHtmlBySelenium(url, waits, request, spider)

    # 获取公司列表页面
    def getCompanies(self, request, spider):
        waits = []
        waits.append(EC.title_contains("EMISPRO - Industries - Companies List"))
        waits.append(EC.presence_of_element_located((By.CSS_SELECTOR, '#acc1 > li:nth-child(4) > h4')))
        return self.getHtmlBySelenium(request.url, waits, request, spider)




    # 获取公司信息并下载附件
    def getCompanyExcel(self, request, spider):
        while (True):
            try:
                # 页面跳转
                waits = []
                waits.append(EC.title_contains("Companies - Company Profile - Tearsheet"))
                self.getHtmlBySelenium(request.url, waits, request, spider)

                # 点击reportbuild
                WebDriverWait(self.browser, self.timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.reportbuilderformlnk')))
                self.browser.find_element_by_class_name("reportbuilderformlnk").click()

                # 点击select all
                WebDriverWait(self.browser, self.timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.select-deselect-all-link')))
                self.browser.find_element_by_class_name("select-deselect-all-link").click()

                # 点击excel下载
                self.browser.find_element_by_class_name("span-excel-2").click()
                WebDriverWait(self.browser, 200).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.download-generated-report')))

                # 获取下载地址
                uid = self.browser.find_element_by_class_name('download-generated-report').get_attribute('data-uid')
                # 获取分类信息
                activities = []
                for item in self.browser.find_elements_by_css_selector(
                        "#wrapper > div.clearfix.ecpr-body > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div li"):
                    activty = item.get_attribute('innerHTML')
                    activities.append(activty[0:activty.index(' (')])

                # 下载文件
                self.browser.find_element_by_class_name('download-generated-report').click()
                # https://www.emis.com/php/companies/reportbuilder/download-generated-report?uid=bd16c996-86c4-4a41-9460-febdd2d46a65
                body = {
                    'url': 'https://www.emis.com/php/companies/reportbuilder/download-generated-report?uid=' + uid,
                    'activities': activities
                }
                # 公司名称
                urlObj = urlparse.urlparse(request.url)
                params = urlparse.parse_qs(urlObj.query)
                companyFileName = None
                
                # 判断文件下载完成
                for i in range(1,90):
                    companyFileName = self.get_company_local_fileName(params['cmpy'][0])
                    if companyFileName:
                        if os.path.isfile(os.path.join(self.downloadPath, companyFileName)):
                            break
                    sleep(2)
                    
                # 移动到对应的目录
                activitiesDir = self.rootPath
                for activity in activities:
                    activitiesDir = os.path.join(activitiesDir, activity)
                if not os.path.isdir(activitiesDir):
                    try:
                        os.makedirs(activitiesDir)
                    except Exception:
                        activitiesDir = os.path.join(self.rootPath, 'error')
                    if not os.path.isdir(activitiesDir):
                        os.makedirs(activitiesDir)

                
                try:
                    shutil.move(os.path.join(self.downloadPath, companyFileName), os.path.join(activitiesDir, companyFileName))
                except Exception:
                    shutil.move(os.path.join(self.downloadPath, companyFileName), os.path.join(os.path.join(self.rootPath, 'error'), companyFileName))
                    
                return HtmlResponse(url=request.url, body=json.dumps(body), request=request, encoding='utf-8', status=200)
            except Exception:
                print "getCompanyExcel error:" + str(Exception)
                traceback.print_exc()
                self.__init__()


    def get_company_local_fileName(self, companyId):
        if companyId:
            for file in os.listdir(self.downloadPath):
                if file.find(companyId) != -1:
                    return file

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest

        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        #try:
        #    self.browser.quit()
        #except Exception:
        #    pass
	pass
	

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)

    # selenium获取数据
    def getHtmlBySelenium(self, url, waits, request, spider):
        while (True):
            try:
                self.browser.get(url)
                # we have to wait for the page to refresh, the last thing that seems to be updated is the title
                for wait in waits:
                    WebDriverWait(self.browser, self.timeout).until(wait)
                return HtmlResponse(url=request.url, body=self.browser.page_source, request=request, encoding='utf-8',
                                    status=200)
            except TimeoutException:
                try:
                    if self.browser.title == 'Login - EMIS':
                        return self.emis_login_retry(url, waits, request, spider)
                    else:
                        return HtmlResponse(url=request.url, status=500, request=request)
                except Exception:
                    traceback.print_exc()
            except Exception:
                print "getHtmlBySelenium error:" + str(Exception)
                traceback.print_exc()
                self.__init__()



    # 登陆并重试
    def emis_login_retry(self, url, waits, request, spider):
        # 登陆成功
        while (True):
            try:
                self.browser.get("https://intellinet.deloitte.com/Secure/Forms/LoadContentProvider.aspx?LinkId=21")
                # we have to wait for the page to refresh, the last thing that seems to be updated is the title
                WebDriverWait(self.browser, self.timeout).until(EC.title_contains("Country Login - EMIS"))
                break
            except TimeoutException:
                try:
                    if self.browser.title == 'My EMIS':
                        break
                except Exception:
                    pass
            except Exception:
                print "emis_login_retry error:" + str(Exception)
                traceback.print_exc()
                self.__init__()

        # 重试
        return self.getHtmlBySelenium(url, waits, request, spider)


if __name__ == "__main__":
    # browser = webdriver.Ie(
    #     executable_path=os.path.abspath(os.path.dirname(os.getcwd())) + '\scrapy_emis\\bin\IEDriverServer.exe')
    # try:
    #     # emis_login(driver)
    #     browser.get("https://www.emis.com/php/companies?pc=CN&cmpy=1732087")
    #
    #     WebDriverWait(browser, 30).until(EC.title_contains("Companies - Company Profile - Tearsheet"))
    #     # print len(browser.find_elements_by_css_selector(
    #     #     "#wrapper > div.clearfix.ecpr-body > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > div > div:nth-child(2) > div:nth-child(1) > div li"))
    #     # for item in browser.find_elements_by_css_selector(
    #     #         "#wrapper > div.clearfix.ecpr-body > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div li"):
    #     #     activty = item.get_attribute('innerHTML')
    #     #     activty = activty[0:activty.index(' (')]
    #     #     print activty
    #     cookies = browser.get_cookies()
    #     print cookies
    # except TimeoutException:
    #     pass
    # finally:
    #     browser.quit()
    urlObj = urlparse.urlparse("https://www.emis.com/php/companies?pc=CN&cmpy=1732088")
    params = urlparse.parse_qs(urlObj.query)
    companyId = params['cmpy'][0]
    print ScrapyEmisDownloaderMiddleware().get_company_local_fileName(companyId)
