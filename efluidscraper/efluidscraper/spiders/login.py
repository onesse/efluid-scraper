# -*- coding: utf-8 -*-
import json

import scrapy
from scrapy import Request
from scrapy.http import FormRequest
import re
import urllib.parse as urlparse
import pandas as pd
import itertools
import tldextract
# from scrapy_splash import SplashRequest, SplashFormRequest

# pycharm peut ne pas comprendre et indiquer une erreur de lib
from efluidscraper.utils import add_url_params, query_string_remove
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError, TCPTimedOutError
from twisted.python.compat import izip
from efluidscraper.const import FORM_DATA_POST_RECHERCHE, FORM_DATA_VISU_ONGLET_VISU_RELEVES, \
    FORM_DATA_RELATION_CLIENT, RelationClient, DomaineTension, TypeTension
from efluidscraper.items import EfluidscraperItem

from efluidscraper.const import FORM_DATA_VISU_RELEVES, Nature



class LoginSpider(scrapy.Spider):
    name = 'login'
    allowed_domains = []
    # start_urls = []
    url = ""
    user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36"
    _rqId_ = 0
    session_id = None
    ns = None
    cs = None
    fs = None
    _nwg_ = None
    lnm = None
    npg = None
    _mnLck_ = None
    abonnementsPortail = None
    list_rae_df = None

    def __init__(self, filename='', **kwargs):

        try:
            with open('./efluidscraper/credentials/ELD.json') as f:
                self.DATA_ELD = json.load(f)
        except IOError:
            raise Exception("Missing ELD access -> please provide JSON credentials")

        # On complète les allowed domains
        for grd in self.DATA_ELD:
            ext = tldextract.extract(self.DATA_ELD[grd]['url'])
            self.allowed_domains.append(ext.subdomain + '.' + ext.domain + '.' + ext.suffix)

        # On récupère le fichier de RAE à parser
        self.list_rae_df = pd.read_excel(filename)
        self.list_rae_df = self.list_rae_df.replace(pd.np.nan, '', regex=True)

        super().__init__(**kwargs)

    def start_requests(self):

        # On va traiter les sites par GRD
        list_grd = pd.unique(self.list_rae_df['grd'])

        for grd in list_grd:
            list_rae_grd_df = self.list_rae_df[self.list_rae_df['grd']==grd]

            # utilisation des metas
            meta = self.DATA_ELD[grd]
            meta['sites'] = list_rae_grd_df
            meta['grd'] = grd
            meta['_rqId_'] = 0

            for idx, row in list_rae_grd_df.iterrows():
                meta['site_en_cours'] = row
                yield Request(url=meta['url'], method='GET', callback=self.recuperation_variables_cachees, meta=meta, dont_filter=True)


    def recuperation_variables_cachees(self, response):
        meta = response.meta
        meta['_rqId_'] += 1

        href_iframe = meta['url_base'] + response.xpath('//iframe[@name="bas"]/@src').extract_first()

        request = Request(url=href_iframe, method='GET', callback=self.login, meta=meta)
        yield request


    def login(self, response):

        meta = response.meta
        meta['_rqId_'] += 1

        self.ns = response.xpath('//input[@name="ns"]/@value').extract_first() or ''
        self.cs = response.xpath('//input[@name="cs"]/@value').extract_first() or ''
        self.fs = response.xpath('//input[@name="fs"]/@value').extract_first() or ''
        meta["session_id"] = query_string_remove(response.url)[-32:]

        formdata = {'lg': meta['login'],
                    'psw': meta['pwd'],
                    'IDB': 'connexion',
                    'frame': 'true',
                    'act': 'valider',
                    '_rqId_': str(meta['_rqId_']),
                    'ns': self.ns,
                    'cs': self.cs,
                    'fs': self.fs,
                    '_nwg_':''}

        response = response.replace(url=query_string_remove(response.url))

        request = FormRequest(url=response.url,
                              method='POST',
                              formdata=formdata,
                              callback=self.parse_after_login,
                              headers={'Referer': 'no-referrer-when-downgrade',},
                              meta=meta
                              )

        yield request


    def parse_after_login(self, response):
        body = response.body.decode('latin-1')

        meta = response.meta
        meta['_rqId_'] += 1

        # récupération du top haut location
        meta["session_id"] = re.search("SESSIONID=(.*)';", body).group(1)
        print(f"L'utilisateur est maintenant connecté avec la session ID : {meta['session_id']}")

        # consulter un point _rqId_=XX&act=demarrer
        new_params = {'_rqId_': str(meta['_rqId_']), 'act': 'demarrer'}

        url = meta['url_base'] + 'ref.RechercherPDS.go' + ';SESSIONID=' + meta["session_id"] + '?'
        url = add_url_params(url, new_params)

        yield Request(url=url, callback=self.creation_post_recherche_point, meta=meta)


    def creation_post_recherche_point(self, response):

        meta = response.meta
        meta['_rqId_'] += 1

        # Il faut découvrir les inputs de type "hidden"...
        self._nwg_ = response.xpath('//input[@name="_nwg_"]/@value').extract_first() or ''
        self.lnm = response.xpath('//input[@name="lnm"]/@value').extract_first() or ''
        self.npg = response.xpath('//input[@name="npg"]/@value').extract_first() or ''
        self._mnLck_ = response.xpath('//input[@name="_mnLck_"]/@value').extract_first() or ''
        self.abonnementsPortail = response.xpath('//select[@name="abonnementsPortail"]/option/@value').extract_first() or ''
        self.ns = response.xpath('//input[@name="ns"]/@value').extract_first() or ''
        self.cs = response.xpath('//input[@name="cs"]/@value').extract_first() or ''
        self.fs = response.xpath('//input[@name="fs"]/@value').extract_first() or ''

        formdata = FORM_DATA_POST_RECHERCHE.copy()
        formdata['_rqId_'] = str(meta['_rqId_'])
        formdata['lnm'] = self.lnm
        formdata['npg'] = self.npg
        formdata['_mnLck_'] = self._mnLck_
        formdata['abonnementsPortail'] = self.abonnementsPortail
        formdata['referencePDS'] = meta['site_en_cours']['rae']

        # Si le PDL contient une clé et que l'on ne la connait pas on va la chercher
        if meta['pds_key']:
            if 'key' in meta['site_en_cours']:
                if meta['site_en_cours']['key'] == '':
                    meta['site_en_cours']['key'] = 10
            else:
                meta['site_en_cours']['key'] = 10
            formdata['clePDS'] = str(meta['site_en_cours']['key'])

        meta['formdata'] = formdata

        # préparation de l'url
        url = query_string_remove(response.url)

        yield FormRequest(url=url,
                          method='POST',
                          formdata=formdata,
                          callback=self.parsing_recherche_point,
                          errback=self.errback,
                          meta=meta)

    def errback(self, failure):
        # log all failures
        self.logger.error(repr(failure))

        if failure.check(HttpError):
            # these exceptions come from HttpError spider middleware
            # you can get the non-200 response
            response = failure.value.response
            self.logger.error('HttpError on %s', response.url)

        elif failure.check(DNSLookupError):
            # this is the original request
            request = failure.request
            self.logger.error('DNSLookupError on %s', request.url)

        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            self.logger.error('TimeoutError on %s', request.url)

    def parsing_recherche_point(self, response):
        # print(response.body.decode('latin-1'))
        message_erreur = response.xpath('//ul[@class="messageErreur"]/li/text()').extract_first() or ''
        print(message_erreur)
        print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
        pattern = "la clé ([0-9]{1,2}|nan) n'est pas valide pour la référence de PDS"
        if re.match(pattern, message_erreur):
            if response.meta['site_en_cours']['key'] is not None:
                formdata = response.meta['formdata']
                response.meta['site_en_cours']['key'] += 1
                formdata['clePDS'] = str(response.meta['site_en_cours']['key'])
                self._rqId_ += 1
                formdata['_rqId_'] = str(self._rqId_)

                yield FormRequest(url=response.url,
                          method='POST',
                          formdata=formdata,
                          callback=self.parsing_recherche_point,
                          errback=self.errback,
                          meta=response.meta)
            else:
                self.logger.error("Aucune clé PDS valide ...")
                item = {'error': "Aucune clé PDS valide ..."}
                return item

        # print(response.body.decode('latin-1'))
        resultat = response.xpath('//div[@class="entete-tableau resultat-recherche"]/span/text()').extract_first()

        if resultat is None or not re.match(r"Résultat : il y a [1-9]{1,2} enregistrement\x28s\x29 correspondant à votre demande", resultat):
            return

        print(f"rae: {response.meta['site_en_cours']['rae']} : {resultat}")

        body = response.body.decode('latin-1')
        colonnes_reponse = response.xpath('//table[@class="miseEnPage"]/tr/td[@class="titreColonne"]/text()').extract()

        _dict_sites = {}
        adict = {}

        has_lines = True
        class_td_result = 'ligne'
        start_index = 1


        while has_lines:
            class_td_result += str(start_index)
            if class_td_result not in body:
                break
            if start_index > 1:
                raise Exception("Multiple results ... Not handled yet !")

            start_index += 1

            values_site = []
            colonne_ligne = response.xpath(f'//td[@class="{class_td_result}"]')
            for i, colonne in enumerate(colonne_ligne):
                if i == 0:
                    onclick = response.xpath(f'//td[@class="{class_td_result}"]/a/@onclick').extract_first()
                    values_site.append(re.search("selIdresultatRecherche.value='(.*)';", onclick).group(1))
                else:
                    values_site.append(colonne.xpath('./input/@value').extract_first() or '')
                    adict = dict(izip(colonnes_reponse, values_site))

            _dict_sites.update(adict)

        df = pd.DataFrame(data=_dict_sites, index=[0])

        if df.shape[0] == 0:
            return

        # Création de l'item
        item = dict()

        # enregistrement des premières informations
        item['reference_id'] = df.iloc[0]['réf.']
        item['pds'] = response.meta['site_en_cours']['rae']
        item['n_voie'] = df.iloc[0]['n°']
        item['voie'] = df.iloc[0]['voie']
        item['commune'] = df.iloc[0]['commune']
        item['ref_compteur'] = df.iloc[0]['réf. compteur']

        if 'key' in response.meta['site_en_cours'] and response.meta['site_en_cours']['key'] != '':
            item['clePDS'] = response.meta['site_en_cours']['key']

        meta = response.meta
        meta['item'] = item
        meta['_rqId_'] += 1

        form_data = self.preparation_request_consultation_point(meta['site_en_cours']['rae'], item['reference_id'], meta['_rqId_'])

        yield FormRequest(url=response.url,
                          method='POST',
                          formdata=form_data,
                          callback=self.handle_relation_client,
                          meta=meta)


    def preparation_request_consultation_point(self, pds: str, id_pds: str, _rqId_: int):
        formdata = FORM_DATA_POST_RECHERCHE.copy()
        formdata['act'] = 'selectionner'
        formdata['_rqId_'] = str(_rqId_)
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

        meta = response.meta
        meta['_rqId_'] += 1

        formdata['_rqId_'] = str(meta['_rqId_'])
        formdata['_mnLck_'] = response.xpath('//input[@name="_mnLck_"]/@value').extract_first()
        formdata['typecontratconcluye'] = str(RelationClient[response.meta["site_en_cours"]["contrat"]].value)
        formdata['numeroContratConcluAvecClient'] = response.meta["site_en_cours"]["ref_relation_client"]
        formdata['dateSignatureContrat'] = response.meta["site_en_cours"]["signature_relation_client"].strftime("%d/%m/%Y")
        formdata['mentionLegaleMandat'] = response.xpath('//textarea[@name="mentionLegaleMandat"]/text()').extract_first() or ''
        formdata['mentionLegaleContratConclu'] = response.xpath('//textarea[@name="mentionLegaleMandat"]/text()').extract_first() or ''

        url = meta['url_base'] + 'ref.ZoomerChoixRelationContratAvecClient.go;SESSIONID=' + meta["session_id"]

        yield FormRequest(url=url,
                          method='POST',
                          formdata=formdata,
                          callback=self.parse_pds_infos,
                          meta=meta)


    def parse_pds_infos(self, response):
        # print(response.body.decode('latin-1'))

        meta = response.meta
        meta['_rqId_'] += 1
        item = meta['item']

        item['reference'] = response.xpath('//input[@name="reference"]/@value').extract_first() or ''
        item['type'] = response.xpath('//input[@name="typeEspacedescr"]/@value').extract_first() or ''
        item['libelle'] = response.xpath('//input[@name="libelle"]/@value').extract_first() or ''
        item['complement'] = response.xpath('//input[@name="complementLocalisation"]/@value').extract_first() or ''
        item['statut'] = response.xpath('//input[@name="statutdescr"]/@value').extract_first() or ''

        item['utilisationdescr'] = response.xpath('//input[@name="utilisationdescr"]/@value').extract_first() or ''
        item['utilisation'] = response.xpath('//input[@name="utilisation"]/@value').extract_first() or ''
        item['dateDeCreation'] =  response.xpath('//input[@name="dateDeCreation"]/@value').extract_first() or ''
        item['dateDeModification'] = response.xpath('//input[@name="dateDeModification"]/@value').extract_first() or ''
        item['dateDeSuppression'] = response.xpath('//input[@name="dateDeSuppression"]/@value').extract_first() or ''

        # Changement d'url
        url = meta['url_base'] + 'ref.ZoomerDossierEDLOElementsTechniques.go;SESSIONID=' + meta["session_id"]

        formdata = {
            'act': 'consulterPDS',
            '_rqId_': str(meta['_rqId_']),
            '_mnLck_': self._mnLck_,
            '_startForm_': '',
            'selIdpointsDeService': item['reference_id'],
            '_endForm_': ''
        }

        yield FormRequest(url=url,
                          method='POST',
                          formdata=formdata,
                          callback=self.parse_pds_infos_2,
                          meta=meta)


    def parse_pds_infos_2(self, response):
        meta = response.meta
        item = meta['item']

        meta['_rqId_'] += 1

        item['reference'] = response.xpath('//input[@name="reference"]/@value').extract_first() or ''
        item['naturedescr'] = response.xpath('//input[@name="naturedescr"]/@value').extract_first() or ''
        item['nature'] = response.xpath('//input[@name="nature"]/@value').extract_first() or ''
        item['sousEtatElec'] = response.xpath('//input[@name="sousEtatElec"]/@value').extract_first() or ''
        item['sousEtatElecdescr'] = response.xpath('//input[@name="sousEtatElecdescr"]/@value').extract_first() or ''

        item['etat'] = response.xpath('//input[@name="etat"]/@value').extract_first() or ''
        item['etatdescr'] = response.xpath('//input[@name="etatdescr"]/@value').extract_first() or ''

        item['grd'] = response.xpath('//input[@name="grd"]/@value').extract_first() or ''

        item['dateEtat'] = response.xpath('//input[@name="dateEtat"]/@value').extract_first() or ''
        item['dateAbandon'] = response.xpath('//input[@name="dateAbandon"]/@value').extract_first() or ''
        item['dateCreation'] = response.xpath('//input[@name="dateCreation"]/@value').extract_first() or ''
        item['dateModification'] = response.xpath('//input[@name="dateModification"]/@value').extract_first() or ''
        item['dateMiseEnService'] = response.xpath('//input[@name="dateMiseEnService"]/@value').extract_first() or ''
        item['adresseEDL'] = response.xpath('//input[@name="adresseEDL"]/@value').extract_first() or ''
        item['complementsLocalisationEDL'] = response.xpath('//input[@name="complementsLocalisationEDL"]/@value').extract_first() or ''


        item['niveauTension'] = DomaineTension(int(response.css('input[name="niveauTension"]:checked::attr(value)').extract_first())).name or ''
        item['typeTension'] = TypeTension(int(response.css('input[name="typeTension"]:checked::attr(value)').extract_first())).name or ''
        item['puisLimiteTechnique'] = response.css('input[name="puisLimiteTechnique"]::attr(value)').extract_first() or ''
        item['puisLimiteTechnique_unit'] = response.css('input[name="puisLimiteTechnique_unit"]::attr(value)').extract_first() or ''
        item['puisLimiteTechnique_unitdescr'] = response.css('input[name="puisLimiteTechnique_unitdescr"]::attr(value)').extract_first() or ''
        item['calibreProtection'] = response.css('input[name="calibreProtection"]::attr(value)').extract_first() or ''
        item['typeProtection'] = response.css('input[name="typeProtection"]::attr(value)').extract_first() or ''
        item['typeProtectiondescr'] = response.css('input[name="typeProtectiondescr"]::attr(value)').extract_first() or ''

        item['modeReleve'] = response.css('input[name="modeReleve"]::attr(value)').extract_first() or ''
        item['modeRelevedescr'] = response.css('input[name="modeRelevedescr"]::attr(value)').extract_first() or ''

        item['emplacementCompteur'] = response.css('input[name="emplacementCompteur"]::attr(value)').extract_first() or ''
        item['emplacementCompteurdescr'] = response.css('input[name="emplacementCompteurdescr"]::attr(value)').extract_first() or ''

        item['certificatConformite'] = response.css('input[name="certificatConformite"]::attr(value)').extract_first() or ''
        item['certificatConformitedescr'] = response.css('input[name="certificatConformitedescr"]::attr(value)').extract_first() or ''

        item['dateProchaineReleve'] = response.css('input[name="dateProchaineReleve"]::attr(value)').extract_first() or ''

        # Click sur l'onglet "relèves"
        formdata = FORM_DATA_VISU_ONGLET_VISU_RELEVES.copy()
        ongclick_str = response.xpath(f'//a[text()="relèves"]/@onclick').extract_first()
        _ongIdx = re.search("_ongIdx.value='(.*)';", ongclick_str).group(1)

        # TODO : optim en travaillant avec les keys des dicts
        formdata['_rqId_'] = str(meta['_rqId_'])
        formdata['_ongIdx'] = _ongIdx
        formdata['grd'] = item['grd']
        formdata['reference'] = item['reference']
        formdata['nature'] = item['nature']
        formdata['naturedescr'] = item['naturedescr']
        formdata['etat'] = item['etat']
        formdata['etatdescr'] = item['etatdescr']
        formdata['sousEtatElec'] = item['sousEtatElec']
        formdata['sousEtatElecdescr'] = item['sousEtatElecdescr']
        formdata['dateEtat'] = item['dateEtat']
        formdata['dateCreation'] = item['dateCreation']
        formdata['dateModification'] = item['dateModification']
        formdata['dateMiseEnService'] = item['dateMiseEnService']
        formdata['dateAbandon'] = item['dateAbandon']
        formdata['adresseEDL'] = item['adresseEDL']
        formdata['complementsLocalisationEDL'] = item['complementsLocalisationEDL']
        formdata['dateProchaineReleve'] = item['dateProchaineReleve']
        formdata['puisLimiteTechnique'] = item['puisLimiteTechnique']
        formdata['puisLimiteTechnique_unit'] = item['puisLimiteTechnique_unit']
        formdata['puisLimiteTechnique_unitdescr'] = item['puisLimiteTechnique_unitdescr']
        formdata['calibreProtection'] = item['calibreProtection']
        formdata['typeProtection'] = item['typeProtection']
        formdata['typeProtectiondescr'] = item['typeProtectiondescr']
        formdata['modeReleve'] = item['modeReleve']
        formdata['modeRelevedescr'] = item['modeRelevedescr']
        formdata['emplacementCompteur'] = item['emplacementCompteur']
        formdata['emplacementCompteurdescr'] = item['emplacementCompteurdescr']
        formdata['certificatConformite'] = item['certificatConformite']
        formdata['certificatConformitedescr'] = item['certificatConformitedescr']

        # Changement d'url
        url = meta['url_base'] + 'ref.ZoomerPDSElecOGeneralites.go;SESSIONID=' + meta["session_id"]


        # print(formdata)
        yield FormRequest(url=url,
                          method='POST',
                          formdata=formdata,
                          callback=self.temp,
                          meta=meta)


    def temp(self, response):
        # print(response.body.decode('latin-1'))
        meta = response.meta
        meta['_rqId_'] += 1

        # Simulation click sur "visualiser relèves"
        formdata = self.preparation_request_releve_donnees(response)

        # Changement d'url
        url = meta['url_base'] + 'releve.ZoomerPDSElecOReleves.go;SESSIONID=' + meta["session_id"]

        yield FormRequest(url=url,
                          method='POST',
                          formdata=formdata,
                          callback=self.parse_pds_releves,
                          meta=meta)

    def preparation_request_releve_donnees(self, response):
        item = response.meta['item']

        formdata = FORM_DATA_VISU_RELEVES.copy()
        formdata['grd'] = item['grd']
        formdata['_rqId_'] = str(response.meta['_rqId_'])
        formdata['_mnLck_'] = self._mnLck_
        formdata['reference'] = item['reference']
        formdata['nature'] = item['nature']
        formdata['naturedescr'] = item['naturedescr']
        formdata['etat'] = item['etat']
        formdata['etatdescr'] = item['etatdescr']
        formdata['sousEtatElec'] = item['sousEtatElec']
        formdata['sousEtatElecdescr'] = item['sousEtatElecdescr']
        formdata['dateEtat'] = item['dateEtat']
        formdata['dateCreation'] = item['dateCreation']
        formdata['dateModification'] = item['dateModification']
        formdata['dateMiseEnService'] = item['dateMiseEnService']
        formdata['adresseEDL'] = item['adresseEDL']
        formdata['complementsLocalisationEDL'] = item['complementsLocalisationEDL']
        return formdata


    def parse_pds_releves(self, response):
        meta = response.meta
        meta['_rqId_'] += 1
        item = meta['item']
        # parsing de toutes les lignes du tableau de la page N
        table_row = response.xpath('//table[@id="tbl_releves"]/tr')

        for row in table_row:
            key = row.xpath('.//td[contains(@class, "leftAligned titreColonne")]/text()').extract_first()
            value = row.xpath('.//td[contains(@class, "leftAligned titreColonne")]/following-sibling::td/text()').extract_first()
            if key is not None and value is not None:
                item[key] = value

        # Récupération des consos annuelles
        url = meta['url_base'] + 'releve.ZoomerPDSElecOReleves.go;SESSIONID=' + meta['session_id']

        # Click sur l'onglet "relèves"
        formdata = FORM_DATA_VISU_ONGLET_VISU_RELEVES.copy()
        ongclick_str = response.xpath(f'//a[text()="consommations mensuelles"]/@onclick').extract_first()
        _ongIdx = re.search("_ongIdx.value='(.*)';", ongclick_str).group(1)

        formdata['_rqId_'] = str(meta['_rqId_'])
        formdata['_ongIdx'] = _ongIdx
        formdata['grd'] = item['grd']
        formdata['reference'] = item['reference']
        formdata['nature'] = item['nature']
        formdata['naturedescr'] = item['naturedescr']
        formdata['etat'] = item['etat']
        formdata['etatdescr'] = item['etatdescr']
        formdata['sousEtatElec'] = item['sousEtatElec']
        formdata['sousEtatElecdescr'] = item['sousEtatElecdescr']
        formdata['dateEtat'] = item['dateEtat']
        formdata['dateCreation'] = item['dateCreation']
        formdata['dateModification'] = item['dateModification']
        formdata['dateMiseEnService'] = item['dateMiseEnService']
        formdata['dateAbandon'] = item['dateAbandon']
        formdata['adresseEDL'] = item['adresseEDL']
        formdata['complementsLocalisationEDL'] = item['complementsLocalisationEDL']
        formdata['dateProchaineReleve'] = item['dateProchaineReleve']
        formdata['puisLimiteTechnique'] = item['puisLimiteTechnique']
        formdata['puisLimiteTechnique_unit'] = item['puisLimiteTechnique_unit']
        formdata['puisLimiteTechnique_unitdescr'] = item['puisLimiteTechnique_unitdescr']
        formdata['calibreProtection'] = item['calibreProtection']
        formdata['typeProtection'] = item['typeProtection']
        formdata['typeProtectiondescr'] = item['typeProtectiondescr']
        formdata['modeReleve'] = item['modeReleve']
        formdata['modeRelevedescr'] = item['modeRelevedescr']
        formdata['emplacementCompteur'] = item['emplacementCompteur']
        formdata['emplacementCompteurdescr'] = item['emplacementCompteurdescr']
        formdata['certificatConformite'] = item['certificatConformite']
        formdata['certificatConformitedescr'] = item['certificatConformitedescr']

        yield FormRequest(url=url,
                          method='POST',
                          formdata=formdata,
                          callback=self.parse_conso_mensuelles,
                          meta=meta)


    def parse_conso_mensuelles(self, response):

        item = response.meta['item']

        tr = response.xpath('//table[@id="tbl_histoConsoMensuelles"]/tr')
        columns_names = tr[0].xpath('.//td[not(@class="paveGaucheListe")]/text()').extract()[1:]
        conso_kWh = tr[1].xpath('.//td/text()').extract()[1:]

        if len(columns_names) != len(conso_kWh):
            raise Exception("Problème de taille sur les données de conso mensuelles")
        else:
            for key, value in zip(columns_names, conso_kWh):
                item[key] = value

        yield item

