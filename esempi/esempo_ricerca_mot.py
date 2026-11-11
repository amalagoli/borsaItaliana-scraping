
""" Test ricerca su MOT """
from dataclasses import asdict, dataclass, fields

import polars as pl

from borsa_italiana_scraping.lista_mot import leggi_catalogo
from borsa_italiana_scraping.ricerca_mot import get_mot_search, lista_cerca_opzioni
from borsa_italiana_scraping.plutils import lista_to_pl
from borsa_italiana_scraping.scheda import ottieni_scheda
from borsa_italiana_scraping.sessione import Sessione

bit_ses = Sessione()

pl_options = lista_cerca_opzioni()
pl_opt_sel = pl_options.filter(pl.col("option_element") == "structure")[["option_label", "selection"]]

search_mot_options = {
    #    "MOT"	                           "MOT"
    #   "Euronext Access Milan"	           "EXTRAMOT"
    #   "Euronext Access Milan Professi…   "EXTRAMOT-PRO"
    #   "Euronext Access Milan Professi…   "EXTRAMOT-PROCUBE"
    "market": "MOT",
    # ------------------------------ #
    #    "Banche"                         "BNC"
    #    "Corporate"                      "CRP"
    #    "Eurobonds Republic Of Italy"	  "ERI"
    #    "Secured"	                      "SEC"
    #    "Titoli Di Stato Esteri"	      "TSE"
    #    "Titoli Di Stato Italiani"	      "TSI"
    "typology": "TSE",  # BNC, CRP, ERI, SEC, TSE, TSI
    # ------------------------------ #
    #    "Index Linked"	         "4"
    #    "Inflation Linked"	     "6"
    #    "Plain Vanilla"	     "1"
    #    "Strutturate Su Tassi"	 "2"
    "structure": "1",
    # ------------------------------ #
    #    "Multi Coupon"          "5"
    #    "One Coupon"            "4"
    #    "Step Coupon"           "9"
    #    "Titolo Con Cedole Tf"  "1"
    #    "Titolo Con Cedole Tv"  "2"
    #    Zero Coupon"            "3"
    # "type": "{s_type}",
    # ------------------------------ #
    # 31/10/2026
    # "expirydatefrom": "{s_exp_date_from_ddmmyyy}",
    # ------------------------------ #
    # 31/10/2026
    # "expirydateto": "{s_exp_date_to_ddmmyyy}",
    # ------------------------------ #
    # See:
    #     pl_options.filter(pl.col("option_element") == "issuer")[["label", "selection"]]
    # "issuer": "{s_issuer}",
    # ------------------------------ #
    # See:
    #     pl_options.filter(pl.col("option_element") == "country")[["label", "selection"]]
    # "country": "{s_country}",
    # ------------------------------ #
    # A numeric value
    # "lot": "{s_lot}",
    # ------------------------------ #
    # See:
    #     pl_options.filter(pl.col("option_element") == "currency")[["label", "selection"]]
    "currency": "EUR",
    # ------------------------------ #
    #    Si'     S
    #    No      N
    # "callable": "N",
    # ------------------------------ #
    #    Si'     "1"
    #    No      "2"
    # "subordination": "2",
    # ------------------------------ #
    # See:
    #     pl_options.filter(pl.col("option_element") == "bondSectorization")[["label", "selection"]]
    # "bondSectorization": "{s_sectorialization}",
    # ------------------------------ #
    # English     en
    # Italiano    it
    "lang": "it",
}

# url_with_page = _build_mot_search_url(search_options)
# pl_test = leggi_lista_pagina(url_with_page.format(page_num="3"), sessione=bit_ses)

# found_listings = get_mot_search(search_mot_options, sessione=bit_ses)

test_isin = 'XS2829741698'
test_scheda = ottieni_scheda(isin=test_isin, lingua='it', sessione=bit_ses)
# Get list of entries
items_list = list(asdict(test_scheda).values())

# MOT catalog
btp_url = 'https://www.borsaitaliana.it/borsa/obbligazioni/mot/btp/lista.html'
btp_list = leggi_catalogo(btp_url, lingua='it', sessione=bit_ses)
pl_btp = lista_to_pl(btp_list)

bot_url = 'https://www.borsaitaliana.it/borsa/obbligazioni/mot/bot/lista.html'
bot_list = leggi_catalogo(bot_url, lingua='it', sessione=bit_ses)
pl_bot = lista_to_pl(bot_list)

eo_url = 'https://www.borsaitaliana.it/borsa/obbligazioni/mot/euro-obbligazioni/lista.html'
eo_list = leggi_catalogo(eo_url, lingua='it', sessione=bit_ses)
pl_eo = lista_to_pl(eo_list)

oe_url = 'https://www.borsaitaliana.it/borsa/obbligazioni/mot/obbligazioni-euro/lista.html'
oe_list = leggi_catalogo(oe_url, lingua='it', sessione=bit_ses)
pl_oe = lista_to_pl(oe_list)
