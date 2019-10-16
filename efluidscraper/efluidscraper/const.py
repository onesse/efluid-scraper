from enum import Enum

FORM_DATA_POST_RECHERCHE = {
    '_nwg_': '',
    'act': 'rechercher',
    '_rqId_': None,
    'lnm': None,
    'npg': None,
    'vurlresultatRecherche': 'null',
    'resultatRecherchepg': '',
    '_mnLck_': None,
    '_startForm_': '',
    'abonnementsPortail': '',
    'referencePDS': '',
    'commune': '',
    'typeVoie': '',
    'voie': '',
    'numero': '',
    'complement': 'VIDE',
    'departement': '',
    'lieudit': '',
    'entree': '',
    'niveau': '',
    'nomOccupantPrecedent': '',
    'prenomOccupantPrecedent': '',
    'referenceCompteur': '',
    'champHidden1': '',
    'champHidden2': '',
    'sortFieldsresultatRecherche': '',
    'sortOrdersresultatRecherche': '',
    'actionSortresultatRecherche': '',
    'selIdresultatRecherche': '',
    'listeDepliee': '',
    '_endForm_': ''
}

FORM_DATA_RELATION_CLIENT = {
    '_nwg_': '',
    'act': 'validerChoixRelationContratAvecClient',
    '_rqId_': None,
    '_mnLck_': 'true',
    '_startForm_': '',
    'typecontratconcluye': '',
    'numeroContratConcluAvecClient': '',
    'dateSignatureContrat': '', # Format DD/MM/YYYY
    'mentionLegaleMandat': '(unable to decode value)',
    'mentionLegaleContratConclu': '(unable to decode value)',
    '_endForm_': ''
}

FORM_DATA_VISU_RELEVES = {
    '_nwg_': '',
    'act': 'visualiserReleves',
    '_rqId_': None,
    '_ongIdx': '',
    '_mnLck_': 'false',
    '_startForm_':'',
    'grd': '',
    'reference': '',
    'nature': '',
    'naturedescr': '',
    'etat': '',
    'etatdescr': '',
    'sousEtatElec': '',
    'sousEtatElecdescr': '',
    'dateEtat': '',
    'dateCreation': '',
    'dateModification': '',
    'dateMiseEnService': '',
    'dateAbandon': '',
    'adresseEDL': '',
    'complementsLocalisationEDL': '',
    'sortFieldslistePACM':'',
    'sortOrderslistePACM':'',
    'actionSortlistePACM':'',
    'selIdlistePACM':'',
    'listeDepliee':'',
    'sortFieldsreleves': '',
    'sortOrdersreleves': '',
    'actionSortreleves': '',
    'selIdreleves': '',
    '_endForm_':''

}

FORM_DATA_VISU_ONGLET_VISU_RELEVES = {
    '_nwg_': '',
    'act': 'afficherOnglet',
    '_rqId_': None,
    '_ongIdx': None,
    '_mnLck_': 'false',
    '_startForm_': '',
    'grd': '',
    'reference': '',
    'nature': '',
    'naturedescr': '',
    'etat': '',
    'etatdescr': '',
    'sousEtatElec': '',
    'sousEtatElecdescr': '',
    'dateEtat': '',
    'dateCreation': '',
    'dateModification': '',
    'dateMiseEnService': '',
    'dateAbandon': '',
    'adresseEDL': '',
    'complementsLocalisationEDL': '',
    'dateProchaineReleve': '',
    'sortFieldsmateriels': '',
    'sortOrdersmateriels': '',
    'actionSortmateriels': '',
    'selIdmateriels': '',
    'listeDepliee': '',
    'puisLimiteTechnique': '',
    'puisLimiteTechnique_unit': '',
    'puisLimiteTechnique_unitdescr': '',
    'calibreProtection': '',
    'typeProtection': '',
    'typeProtectiondescr': '',
    'modeReleve': '',
    'modeRelevedescr': '',
    'emplacementCompteur': '',
    'emplacementCompteurdescr': '',
    'certificatConformite': '',
    'certificatConformitedescr': '',
    '_endForm_':''
}

class RelationClient(Enum):
    CONTRAT_CONCLU = 0
    MANDAT = 1
    AUCUN = 2


class DomaineTension(Enum):
    HTB = 0
    HTA = 1
    BT_P = 2
    BT = 3

class TypeTension(Enum):
    MONOPHASE = 1
    TRIPHASE = 2

class Nature(Enum):
    CONSOMMATION = 1
    PRODUCTION = 2

    @staticmethod
    def from_str(label):
        if label in ('consommation', 'Consommation', 'CONSOMMATION'):
            return Nature.CONSOMMATION
        elif label in ('production', 'Production', 'PRODUCTION'):
            return Nature.PRODUCTION
        else:
            raise NotImplementedError
