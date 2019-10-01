# -*- coding: utf-8 -*-
import scrapy


class LoginSpider(scrapy.Spider):
    name = 'login'
    allowed_domains = ['portailfr.geg-grd.fr']
    start_urls = ['http://portailfr.geg-grd.fr/']

    def parse(self, response):
        pass
