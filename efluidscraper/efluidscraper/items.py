# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class EfluidscraperItem(scrapy.Item):
    # define the fields for your item here like:
    reference_id = scrapy.Field()
    pds = scrapy.Field()
    nature = scrapy.Field()
    naturedescr = scrapy.Field()
    n_voie = scrapy.Field()
    voie = scrapy.Field()
    commune = scrapy.Field()
    ref_compteur = scrapy.Field()

    reference = scrapy.Field()
    type = scrapy.Field()
    libelle = scrapy.Field()
    complement = scrapy.Field()
    statut = scrapy.Field()
    etat = scrapy.Field()
    etatdescr = scrapy.Field()
    utilisationdescr = scrapy.Field()
    utilisation = scrapy.Field()

    dateDeModification = scrapy.Field()
    dateDeSuppression = scrapy.Field()
    dateDeCreation = scrapy.Field()

    niveauTension = scrapy.Field()
    typeTension = scrapy.Field()

    puisLimiteTechnique = scrapy.Field()
    puisLimiteTechnique_unit = scrapy.Field()
    puisLimiteTechnique_unitdescr = scrapy.Field()
    calibreProtection = scrapy.Field()
    typeProtection = scrapy.Field()
    typeProtectiondescr = scrapy.Field()
    modeReleve = scrapy.Field()
    modeRelevedescr = scrapy.Field()

    emplacementCompteur = scrapy.Field()
    emplacementCompteurdescr = scrapy.Field()

    certificatConformite = scrapy.Field()
    certificatConformitedescr = scrapy.Field()

    dateProchaineReleve = scrapy.Field()

    sousEtatElec = scrapy.Field()
    sousEtatElecdescr = scrapy.Field()

    dateEtat = scrapy.Field()
    dateCreation = scrapy.Field()
    dateModification = scrapy.Field()
    dateMiseEnService = scrapy.Field()
    dateAbandon = scrapy.Field()

    adresseEDL = scrapy.Field()
    complementsLocalisationEDL = scrapy.Field()

    grd = scrapy.Field()
    conso = scrapy.Field()

