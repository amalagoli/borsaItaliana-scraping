"""Monitora schede NOT FOUND che sembrano esistere"""

from urllib.parse import urlencode

import polars as pl

from .lista import leggi_lista_pagina
from .sessione import Sessione

# __URL_BIT_SEARCH_SAMPLE = "https://www.borsaitaliana.it/borsa/obbligazioni/advanced-search.html?market=MOT&typology=CRP&structure=1&type=5&expirydatefrom=31/12/2026&expirydateto=30/11/2031&issuer=1634&country=92&lot=1000&currency=EUR&callable=N&subordination=2&bondSectorization=ESG%20Green%20/%20Environmental,ESG%20General,ESG%20Social&lang=it"
__URL_BIT_SEARCH_BASE = "https://www.borsaitaliana.it/borsa/obbligazioni/advanced-search.html"
__URL_BIT_SEARCH_BASE_IT = "https://www.borsaitaliana.it/borsa/obbligazioni/ricerca-avanzata.html"
_URL_TMP = "https://www.borsaitaliana.it/borsa/obbligazioni/advanced-search.html?market=MOT&structure=1&expirydatefrom=31/12/2026&expirydateto=30/11/2031&country=92&currency=EUR&subordination=2&lang=it&page=4"
"""
https://www.borsaitaliana.it/borsa/obbligazioni/advanced-search.html
market=MOT
typology=CRP
structure=1
type=5
expirydatefrom=31/12/2026
expirydateto=30/11/2031
issuer=1634
country=92
lot=1000
currency=EUR
callable=N
subordination=2
bondSectorization=ESG%20Green%20/%20Environmental,ESG%20General,ESG%20Social
lang=it"

"""
__PARAMS_SEARCH_ = {
    "market": "{s_market}",
    "typology": "{s_tipology}",
    "structure": "{s_structure}",
    "type": "{s_type}",
    "expirydatefrom": "{s_exp_date_from_ddmmyyy}",
    "expirydateto": "{s_exp_date_to_ddmmyyy}",
    "issuer": "{s_issuer}",
    "country": "{s_country}",
    "lot": "{s_lot}",
    "currency": "{s_currecny}",
    "callable": "{s_callable}",
    "subordination": "{s_subordination}",
    "bondSectorization": "{s_sectorialization}",
    "lang": "{s_lingua}",
}

__OPTIONS_LABELS = {
    "Mercato": "market",
    "Valuta": "currency",
    "Paese": "country",
    "Tipologia": "typology",
    "Rimborso Anticipato": "callable",
    "Tipo Cedola": "type",
    "Subordinazione": "subordination",
    "Struttura": "structure",
    "Emittente": "issuer",
    "Tipologia di emissione": "bondSectorization",
}

# https://www.borsaitaliana.it/borsa/obbligazioni/advanced-search.html?market=MOT&typology=CRP&structure=1&type=5&country=13&lot=1000&currency=EUR&callable=S&subordination=1&bondSectorization=ESG%20General,ESG%20Social&lang=it

# function submitSearchForm(){
# 		var marketValue = (document.getElementById('markets')).value;
# 		var market = composeUrl("market", marketValue);
# 		var typeValue = (document.getElementById('types')).value;
# 		var type =  composeUrl("type", typeValue);
# 		var typologyValue = (document.getElementById('typologies')).value;
# 		var typology = composeUrl("typology", typologyValue);
# 		var stuctureValue = (document.getElementById('structures')).value;
# 		var structure = composeUrl("structure",stuctureValue);
# 		var datefromValue = (document.getElementById('altExpirationDateFrom')).value;
# 		var expirydatefrom =  composeUrl("expirydatefrom", datefromValue);
# 		var datetoValue =(document.getElementById('altExpirationDateTo')).value;
# 		var expirydateto = composeUrl("expirydateto",datetoValue);
# 		var issuerValue = (document.getElementById('issuers')).value;
# 		var issuer = composeUrl("issuer",issuerValue);
# 		var lotValue = (document.getElementById('lotSize')).value;
# 		var lot = composeUrl("lot",lotValue);
# 		var countryValue = (document.getElementById('countries')).value;
# 		var country = composeUrl("country",countryValue);
# 		var currencyValue = (document.getElementById('currencies')).value;
# 		var currency = composeUrl("currency",currencyValue);
# 		var callableValue = (document.getElementById('callable')).value;
# 		var callable = composeUrl("callable",callableValue);
# 		var subordinationValue = (document.getElementById('subordination')).value;
# 		var subordination = composeUrl("subordination",subordinationValue);
# 		var sectorizationValue = (document.getElementById('hiddenSectorization')).value;
# 		var sectorization = composeUrl("bondSectorization",sectorizationValue);
# 		var lang = "it";

# 		onLoadingTableResults();
# 		var queryString = "?" + market + typology + structure + type + expirydatefrom + expirydateto + issuer + country + lot + currency + callable + subordination+ sectorization +  "lang=" + lang;
# 		jQuery('#tableResults').load('/borsa/obbligazioni/advanced-search.html' + encodeURI(queryString));
# 	}


def lista_cerca_opzioni(sessione: Sessione | None = None) -> pl.DataFrame:
    """Scarica la lista di opzioni nella forma di ricerca"""

    url_with_form = __URL_BIT_SEARCH_BASE_IT

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
        pl_mot_options = pl.concat(l_options)
        pl_mot_options = pl_mot_options.with_columns(
            pl.col("option").map_elements(__OPTIONS_LABELS.get, return_dtype=pl.String).alias("option_element")
        )
    finally:
        if sessione_locale:
            sessione_.chiudi()
    return pl_mot_options


def _build_mot_search_url(search_opts: dict | None = None) -> str:
    """Costruisci una URL di ricerca per obbligazioni"""
    url_base = __URL_BIT_SEARCH_BASE

    if search_opts is None:
        search_url = url_base + "?page={page_num}"
    else:
        # search_opts = dict(search_opts, page="{page_num}")
        params_str = urlencode(search_opts)
        search_url = url_base + "?" + params_str + "&page={page_num}"
    return search_url


def get_mot_search(search_options: dict | None = None, sessione: Sessione | None = None, verbose: bool = False) -> list:
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
        s_url = _build_mot_search_url(search_options)
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
    bit_ses = Sessione()

    pl_options = lista_cerca_opzioni()
    pl_opt_sel = pl_options.filter(pl.col("option_element") == "structure")[["label", "selection"]]

    search_mot_options = {
        #    "MOT"	                           "MOT"
        #   "Euronext Access Milan"	           "EXTRAMOT"
        #   "Euronext Access Milan Professi…   "EXTRAMOT-PRO"
        #   "Euronext Access Milan Professi…   "EXTRAMOT-PROCUBE"
        "market": "EXTRAMOT",
        # ------------------------------ #
        # "typology": "CRP",  # BNC, CRP, ERI, SEC, TSE, TSI
        #    "Index Linked"	         "4"
        #    "Inflation Linked"	     "6"
        #    "Plain Vanilla"	     "1"
        #    "Strutturate Su Tassi"	 "2"
        # "structure": "{s_structure}",
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

    found_listings = get_mot_search(search_mot_options, sessione=bit_ses)
