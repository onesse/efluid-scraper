# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class EfluidscraperItem(scrapy.Item):
    # define the fields for your item here like:
    id_reference = scrapy.Field()
    pds = scrapy.Field()
    conso_prod = scrapy.Field()
    numero_rue = scrapy.Field()
    voie = scrapy.Field()
    commune = scrapy.Field()
    ref_compteur = scrapy.Field()

