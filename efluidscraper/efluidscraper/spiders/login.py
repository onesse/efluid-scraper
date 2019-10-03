# -*- coding: utf-8 -*-
import scrapy
from scrapy import Request
from scrapy.http import FormRequest
import re
import urllib.parse as urlparse
import pandas as pd
import itertools

from scrapy_splash import SplashRequest, SplashFormRequest

# pycharm peut ne pas comprendre et indiquer une erreur de lib
from efluidscraper.utils import add_url_params, query_string_remove
from twisted.python.compat import izip
from efluidscraper.const import FORM_DATA_POST_RECHERCHE, FORM_DATA_RELATION_CLIENT, RelationClient


class LoginSpider(scrapy.Spider):
    name = 'login'
    allowed_domains = ['portailfr.geg-grd.fr']
    start_urls = ['https://portailfr.geg-grd.fr/efluidnetPROD/jsp/arc/commun/frame.jsp']
    url = "https://portailfr.geg-grd.fr/efluidnetPROD/jsp/arc/commun/"
    user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36"
    _rqId_ = None
    session_id = None
    ns = None
    cs = None
    fs = None
    _nwg_ = None
    lnm = None
    npg = None
    _mnLck_ = None
    abonnementsPortail = None

    def start_requests(self):
        for i, url in enumerate(self.start_urls):
            print(f"1******** {url}")
            yield Request(url=url, method='GET', callback=self.recuperation_variables_cachees)

    def recuperation_variables_cachees(self, response):
        href_iframe = self.url + response.xpath('//iframe[@name="bas"]/@src').extract_first()
        print(f"2******** {href_iframe}")
        headers = {'Referer': self.start_urls[0],
                   'Host': 'portailfr.geg-grd.fr',
                   'Sec-Fetch-Mode': 'nested-navigate',
                   'Sec-Fetch-Site': 'same-origin',
                   'Upgrade-Insecure-Requests': '1',
                   'User-Agent': self.user_agent}
        request = Request(url=href_iframe, headers=headers, method='GET', callback=self.login)
        yield request

    def login(self, response):

        self._rqId_ = response.xpath('//input[@name="_rqId_"]/@value').extract_first()
        self.ns = response.xpath('//input[@name="ns"]/@value').extract_first()
        self.cs = response.xpath('//input[@name="cs"]/@value').extract_first()
        self.fs = response.xpath('//input[@name="fs"]/@value').extract_first()
        self.session_id = query_string_remove(response.url)[-32:]

        # TODO : à supprimer
        mot_de_passe = "il96mQ7F"
        login = "hydroption"

        formdata = {'lg': login,
                    'psw': mot_de_passe,
                    'IDB': 'connexion',
                    'frame': 'true',
                    'act': 'valider',
                    '_rqId_': self._rqId_,
                    'ns': self.ns,
                    'cs': self.cs,
                    'fs': self.fs,
                    '_nwg_':''}

        response = response.replace(url=query_string_remove(response.url))

        request = FormRequest(url=response.url,
                              method='POST',
                              formdata=formdata,
                              callback=self.parse_after_login,
                              headers={'Referer': 'no-referrer-when-downgrade',}
                              )

        yield request


    def parse_after_login(self, response):
        body = response.body.decode('latin-1')

        # récupération du top haut location
        self.session_id = re.search("SESSIONID=(.*)';", body).group(1)
        print(f"L'utilisateur est maintenant connecté avec la session ID : {self.session_id}")

        # consulter un point _rqId_=XX&act=demarrer
        new_params = {'_rqId_': self._rqId_, 'act': 'demarrer'}

        url = self.url + 'ref.RechercherPDS.go' + ';SESSIONID=' + self.session_id + '?'
        url = add_url_params(url, new_params)

        yield Request(url=url, callback=self.creation_post_recherche_point)


    def creation_post_recherche_point(self, response):

        # Il faut découvrir les inputs de type "hidden"...
        self._nwg_ = response.xpath('//input[@name="_nwg_"]/@value').extract_first()
        self.lnm = response.xpath('//input[@name="lnm"]/@value').extract_first()
        self.npg = response.xpath('//input[@name="npg"]/@value').extract_first()
        self._mnLck_ = response.xpath('//input[@name="_mnLck_"]/@value').extract_first()
        self._rqId_ = response.xpath('//input[@name="_rqId_"]/@value').extract_first()
        self.abonnementsPortail = response.xpath('//select[@name="abonnementsPortail"]/option/@value').extract_first()
        self.ns = response.xpath('//input[@name="ns"]/@value').extract_first()
        self.cs = response.xpath('//input[@name="cs"]/@value').extract_first()
        self.fs = response.xpath('//input[@name="fs"]/@value').extract_first()

        # TODO: à supprimer
        pds = '18393EC1' # référence PDS example

        formdata = FORM_DATA_POST_RECHERCHE.copy()
        formdata['_rqId_'] = self._rqId_
        formdata['lnm'] = self.lnm
        formdata['npg'] = self.npg
        formdata['_mnLck_'] = self._mnLck_
        formdata['abonnementsPortail'] = self.abonnementsPortail
        formdata['referencePDS'] = pds

        url = query_string_remove(response.url)

        yield FormRequest(url=url,
                          method='POST',
                          formdata=formdata,
                          callback=self.parsing_recherche_point)


    def parsing_recherche_point(self, response):
        resultat = response.xpath('//div[@class="entete-tableau resultat-recherche"]/span/text()').extract_first()
        print("**********************************************")
        print(resultat)
        print("**********************************************")

        body = response.body.decode('latin-1')

        colonnes_reponse = response.xpath('//table[@class="miseEnPage"]/tr/td[@class="titreColonne"]/text()').extract()
        _dict_sites = {}

        has_lines = True
        class_td_result = 'ligne'
        start_index = 1
        list_index = []

        while has_lines:
            class_td_result += str(start_index)
            if class_td_result not in body:
                break
            start_index += 1
            onclick = response.xpath(f'//td[@class="{class_td_result}"]/a/@onclick').extract_first()
            list_index.append(re.search("selIdresultatRecherche.value='(.*)';", onclick).group(1))

            values_site = [response.xpath(f'//td[@class="{class_td_result}"]/a/text()').extract()]
            values_site = values_site + list(map(lambda el:[el], response.xpath(f'//td[@class="{class_td_result}"]/input/@value').extract()))

            adict = dict(izip(colonnes_reponse, values_site))
            _dict_sites.update(adict)

        df = pd.DataFrame(data=_dict_sites, index=list_index)

        print(df)

        for id_recherche, row in df.iterrows():
            form_data = self.preparation_request_consultation_point(row['réf.'], id_recherche)
            yield FormRequest(url=response.url,
                          method='POST',
                          formdata=form_data,
                          callback=self.handle_relation_client)


    def preparation_request_consultation_point(self, pds: str, id_pds: str):
        formdata = FORM_DATA_POST_RECHERCHE.copy()
        formdata['act'] = 'selectionner'
        formdata['_rqId_'] = self._rqId_
        formdata['lnm'] = 'resultatRecherche'
        formdata['npg'] = self.npg
        formdata['_mnLck_'] = self._mnLck_
        formdata['abonnementsPortail'] = self.abonnementsPortail
        formdata['referencePDS'] = pds
        formdata['vurlresultatRecherche'] = 'null'
        formdata['selIdresultatRecherche'] = id_pds
        return formdata

    def handle_relation_client(self, response):
        formdata = FORM_DATA_RELATION_CLIENT.copy()

        formdata['_rqId_'] = self._rqId_
        formdata['_mnLck_'] = self._mnLck_
        formdata['typecontratconcluye'] = str(RelationClient.AUCUN.value)

        url = self.url + 'ref.ZoomerChoixRelationContratAvecClient.go;SESSIONID=' + self.session_id

        print(formdata)
        print(url)
        print("*******************************************************")

        yield FormRequest(url=url,
                          method='POST',
                          formdata=formdata,
                          callback=self.parse_pds_infos)

    def parse_pds_infos(self, response):
        print(response.body.decode('latin-1'))
        # print(href_iframe)
    # print("******************")
    # iframe_html = response.data['childFrames']
    # print(iframe_html)
    # print("___________________")
    # for test in response.css("div.connexion-page"):
    #     print(test.css("div.connexion-ligne::text"))



    # mot_de_passe = "il96mQ7F"
    # login = "hydroption"
    #
    # url = "https://portailfr.geg-grd.fr/efluidnetPROD/jsp/arc/commun/habilitation.ActorIdentification.go;SESSIONID=" + cession_id

    # response = response.replace(url=url)
    # print(response.url)
    # print("***********")
    #
    #

