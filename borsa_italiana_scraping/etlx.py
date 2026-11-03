"""Ricerca obbligazioni EuroTLX"""

from urllib.parse import urlencode

import polars as pl

from .lista import leggi_lista_pagina
from .sessione import Sessione

__URL_TLX_SEARCH_BASE_IT = "https://www.borsaitaliana.it/borsa/obbligazioni/eurotlx/ricerca-avanzata.html"
# function submitSearchForm(){
# 		var categoryValue = (document.getElementById('category')).value;
# 		var category = composeUrl("category", categoryValue);
# 		var datefromValue = (document.getElementById('altExpirationDateFrom')).value;
# 		var expirydatefrom =  composeUrl("expirationDateFrom", datefromValue);
# 		var datetoValue =(document.getElementById('altExpirationDateTo')).value;
# 		var expirydateto = composeUrl("expirationDateTo",datetoValue);
# 		var isinValue = (document.getElementById('isin')).value;
# 		var isin = composeUrl("isin",isinValue);
# 		var issuerValue = (document.getElementById('issuer')).value;
# 		var issuer = composeUrl("issuer",issuerValue);
# 		var currencyValue = (document.getElementById('currency')).value;
# 		var currency = composeUrl("currency",currencyValue);
# 		var sectorizationValue = (document.getElementById('hiddenSectorization')).value;
# 		var sectorization = composeUrl("bondSectorization",sectorizationValue);
# 		var lang = "it";

# 		onLoadingTableResults();
# 		var queryString = "?" + category + expirydatefrom + expirydateto + isin + issuer + currency + sectorization + "lang=" + lang;
# 		jQuery('#tableResults').load('/borsa/obbligazioni/eurotlx/ricerca-avanzata/risultati.html' + encodeURI(queryString));
# 	}
__URL_TLX_SEARCH_BASE = "https://www.borsaitaliana.it/borsa/obbligazioni/eurotlx/ricerca-avanzata/risultati.html"

__OPTIONS_LABELS = {
    "Tipologia": "category",
    "Valuta": "currency",
    "Emittente": "issuer",
    "Tipologia di emissione": "bondSectorization",
}


def lista_tlx_opzioni(sessione: Sessione | None = None) -> pl.DataFrame:
    """Scarica la lista di opzioni nella forma di ricerca"""

    url_with_form = __URL_TLX_SEARCH_BASE_IT

    if not isinstance(sessione, Sessione):
        sessione_ = Sessione()
        sessione_locale = True
    else:
        sessione_ = sessione
        sessione_locale = False

    try:
        soup = sessione_.get_html(url_with_form)

        div_tags = soup.find_all("div", class_="m-form__dropdown")
        drowpdown_inputs_names = [h4.get_text() for h4 in [h4t.find("h4") for h4t in div_tags]]

        sel_labels = ["" if h4 is None else h4.attrs["id"] for h4 in [h4t.find("select") for h4t in div_tags]]

        labels = [[t.get_text().strip() for t in opt] for opt in [h4t.find_all("option") for h4t in div_tags]]
        values = [[t.attrs["value"].strip() for t in opt] for opt in [h4t.find_all("option") for h4t in div_tags]]

        n_labs = len(labels)
        l_options = []
        for nl in range(n_labs):
            opt_name_ = drowpdown_inputs_names[nl]
            opt_sel_ = sel_labels[nl]
            opt_type_ = labels[nl]
            vals_ = values[nl]
            pl_opt_ = pl.DataFrame(
                {
                    "option": opt_name_.strip(),
                    "option_label": opt_sel_,
                    "selection_label": opt_type_,
                    "selection": vals_,
                }
            ).filter(pl.col("selection") != "")
            l_options.append(pl_opt_)
        pl_tlx_options = pl.concat(l_options)
        # pl_tlx_options = pl_tlx_options.with_columns(
        #    pl.col("option")
        #    .map_elements(lambda x: __OPTIONS_LABELS.get(x), return_dtype=pl.String)
        #    .alias("option_element")
        # )
    finally:
        if sessione_locale:
            sessione_.chiudi()
    return pl_tlx_options


# ?category=BOT&expirationDateFrom=20271130&expirationDateTo=20321130&currency=EUR&lang=it
def _build_tlx_search_url(search_opts: dict | None = None) -> str:
    """Costruisci una URL di ricerca per obbligazioni"""
    url_base = __URL_TLX_SEARCH_BASE

    if search_opts is None:
        search_url = url_base + "?page={page_num}"
    else:
        # search_opts = dict(search_opts, page="{page_num}")
        params_str = urlencode(search_opts)
        search_url = url_base + "?" + params_str + "&page={page_num}"
    return search_url


def get_tlx_search(search_options: dict | None = None, sessione: Sessione | None = None, verbose: bool = False) -> list:
    """Collect list of bonds from search on the EuroTLX market"""
    # TODO: add search_options validator
    if not isinstance(sessione, Sessione):
        sessione_ = Sessione()
        sessione_locale = True
    else:
        sessione_ = sessione
        sessione_locale = False
    bond_list = []
    try:
        s_url = _build_tlx_search_url(search_options)
        page_num = 1
        reslist = ["start"]
        while len(reslist) > 0:
            reslist = leggi_lista_pagina(s_url.format(page_num=str(page_num)), sessione=sessione_)
            if len(reslist) > 0:
                bond_list.extend(reslist)
            if verbose:
                print("Page: " + str(page_num))
            page_num += 1
    finally:
        if sessione_locale:
            sessione_.close()
    return bond_list


if __name__ == "main":
    pl_tlx_opts = lista_tlx_opzioni()

    SEARCH_CATEGORY = "Bond"
    pl_search_filter = pl_search_filter.filter(
        (pl.col("option_label") == "category") & (pl.col("selection_label").str.find(search_category) > 0)
    )[["selection_label", "selection"]]

    tlx_search_options = {
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
        # English     en
        # Italiano    it
        "lang": "it",
    }

    bit_sessione = Sessione()

    ret_list = get_tlx_search(tlx_search_options, sessione=bit_sessione)

    # s_url = _build_tlx_search_url(tlx_search_options)
