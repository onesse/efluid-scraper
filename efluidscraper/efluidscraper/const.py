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
    'abonnementsPortail': None,
    'referencePDS': None,
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

class RelationClient(Enum):
    CONTRAT_CONCLU = 0
    MANDAT = 1
    AUCUN = 2
