
""" Test ricerca su EuroTLX """
from dataclasses import asdict, dataclass, fields

import polars as pl

from borsa_italiana_scraping.lista_mot import leggi_catalogo
from borsa_italiana_scraping.plutils import lista_to_pl
from borsa_italiana_scraping.ricerca_etlx import get_etlx_search, lista_etlx_opzioni
from borsa_italiana_scraping.scheda import ottieni_scheda
from borsa_italiana_scraping.sessione import Sessione

bit_ses = Sessione()

pl_etlx_opts = lista_etlx_opzioni()

SEARCH_CATEGORY = "Bond"
# pl_search_filter = pl_search_filter.filter(
#     (pl.col("option_label") == "category") & (pl.col("selection_label").str.find(search_category) > 0)
# )[["selection_label", "selection"]]

etlx_search_options = {
    # ------------------------------ #
    # See:
    #     pl_tlx_opts.filter(pl.col("option_label") == 'category')[["selection_label", "selection"]]
    "category": "T-BONDS",
    # ------------------------------ #
    # 20271130
    # "expirationDateFrom": "{YYYYMMDD}",
    # ------------------------------ #
    # 20321130
    # "expirationDateTo": "{YYYYMMDD}",
    # ------------------------------ #
    # See:
    #     pl_options.filter(pl.col("option_element") == "issuer")[["label", "selection"]]
    # "issuer": "{s_issuer}",
    # ------------------------------ #       # See:
    #     pl_options.filter(pl.col("option_element") == "currency")[["label", "selection"]]
    "currency": "USD",
    # ------------------------------ #
    # See:
    #     pl_options.filter(pl.col("option_element") == "bondSectorization")[["label", "selection"]]
    # "bondSectorization": "{s_sectorialization}",
    # ------------------------------ #

}

bit_ses = Sessione()

etlx_list = get_etlx_search(etlx_search_options, lingua='it', sessione=bit_ses)
pl_cat_etlx = lista_to_pl(etlx_list)

test_isin = 'US912810UJ50'
test_scheda = ottieni_scheda(isin=test_isin, lingua = 'it', platform='TLX', sessione=bit_ses)
