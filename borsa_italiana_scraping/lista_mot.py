"""Scraping delle liste strumenti (BTP, BOT, ecc.) da Borsa Italiana."""

from __future__ import annotations

import time

import polars as pl

from .eccezioni import DatiNonDisponibili
from .lista import (
    _estrai_strumenti,
    _ha_pagina_successiva,
)
from .plutils import lista_to_pl
from .sessione import Sessione
from .tipi import StrumentoLista

# URL lista BTP
_URL_LISTA_BTP = (
    "https://www.borsaitaliana.it/borsa/obbligazioni/mot/btp/lista.html"
)

_URL_LISTA_MOT = "https://www.borsaitaliana.it/borsa/obbligazioni/{mercato_}/lista.html"

_MOT_MARKETS = {
    "Domestic": "mot/obbligazioni-euro",
    "Euro": "mot/euro-obbligazioni",
    "Bot": "mot/bot",
    "Btp": "mot/btp",
    "CCT": "mot/cct",
    "Green e Social Bond": "green-e-social-bond"
}

# The list is split into pages of 20 rows (?page=N): 12 pages in November 2026.
_MAX_PAGINE_LISTA = 200
_PAUSA_TRA_PAGINE = 1.0

def catalogo_mot(
    lingua: str = "it",
    sessione: Sessione | None = None,
    pausa_tra_pagine: float =  _PAUSA_TRA_PAGINE
) -> pl.DataFrame:
    """
    Crea un catalogo dei principali mercati MOT.
    Le URLs sono del tipo: https://www.borsaitaliana.it/borsa/obbligazioni/{mercato_}/lista.html
    dove mercato_ e' uno di:
        "Domestic": "mot/obbligazioni-euro",
        "Euro": "mot/euro-obbligazioni",
        "Bot": "mot/bot",
        "Btp": "mot/btp",
        "CCT": "mot/cct",
        "Green e Social Bond": "green-e-social-bond"

    Args:
        lingua (str): 'it' per italiano - 'en' per inglese.
        sessione (Sessione): una sessione di borsa_italiana_scraping
                             gia' aperta, o None (apre una sessione interna).
        pausa_tra_pagine (float): la pausa, in secondi, tra una pagina e un'altra.

    Returns:s
        Un Polars dataframe con la lista dei prodotti trovati.
    """
    lingua = lingua.lower()
    sessione_locale = sessione is None
    if sessione_locale:
        sessione_ = Sessione()
    else:
        sessione_ = sessione

    try:
        l_cat: list[pl.DataFrame] = []
        for k, u in enumerate(_MOT_MARKETS):
            print(_MOT_MARKETS[u])
            mkt_url = _URL_LISTA_MOT.format(mercato_= _MOT_MARKETS[u])
            bond_list = leggi_catalogo(mkt_url, lingua=lingua, sessione=sessione_)
            pl_cat = lista_to_pl(bond_list)
            pl_cat = pl_cat.with_columns(pl.lit(u, dtype=pl.String).alias("market_group"))
            l_cat.append(pl_cat)
    finally:
        if sessione_locale:
            sessione_.chiudi()
    return pl.concat(l_cat)


def leggi_catalogo(
    url_mercato: str | None,
    lingua: str = "it",
    sessione: Sessione | None = None,
    pausa_tra_pagine: float =  _PAUSA_TRA_PAGINE
) -> list[StrumentoLista]:
    """Ottiene la lista da una pagina di obbligazioni quotate sul MOT.

    Esegue lo scraping della tabella HTML dei BTP. Il sito la divide in pagine
    da 20 righe (``?page=N``): le legge tutte, una dopo l'altra, e si ferma
    quando il paginatore non ha una pagina successiva, quando una pagina è vuota
    o ripete ISIN già letti, oppure dopo ``max_pagine`` pagine.

    Esegue lo scraping di una pagina HTML con la tabella di obbligazioni.

    Args:
        url_mercato (str): la URL del mercato da catalogare. P.es.:
                           https://www.borsaitaliana.it/borsa/obbligazioni/mot/btp/lista.html
        pagina (int|str): il numero della pagina
        lingua: ``"en"`` o ``"it"``.
        sessione: sessione HTTP riutilizzabile.
        max_pagine: numero massimo di pagine da leggere (limite di sicurezza).
        pausa_tra_pagine: secondi di attesa fra una pagina e la successiva,
            oltre alla pausa minima della ``Sessione``.

    Returns:
        Lista di ``StrumentoLista``, uno per ogni BTP (senza duplicati).

    Raises:
        DatiNonDisponibili: se la prima pagina non contiene la tabella o la
            tabella è vuota, oppure se una pagina successiva non contiene la
            tabella (probabile blocco del WAF: la lista sarebbe incompleta).
    """
    lingua = lingua.lower()
    sessione_locale = sessione is None
    if sessione_locale:
        sessione = Sessione()

    market_url = url_mercato  # _URL_LISTA_MOT.format(mercato_=mercato)

    try:
        risultati: list[StrumentoLista] = []
        isin_visti: set[str] = set()

        max_pagine = _MAX_PAGINE_LISTA
        for pagina in range(1, max_pagine + 1):
            parametri = {"lang": lingua}
            # If url already has parameters
            if url_mercato.find("?") > 0:
                market_url = url_mercato + f'&lang={lingua}'
            else:
                market_url = url_mercato + f'?lang={lingua}'
            if pagina > 1:
                parametri["page"] = str(pagina)
                market_url = market_url + f'&page={str(pagina)}'
                if pausa_tra_pagine > 0:
                    time.sleep(pausa_tra_pagine)
            soup = sessione.get_html(market_url)
            # Cerca la tabella principale
            tabella = soup.find("table")
            if not tabella:
                    if pagina == 1:
                        raise DatiNonDisponibili("Tabella BTP non trovata nella pagina")
                    # Past the last page the site still returns the (empty) table:
                    # a page without any table is a WAF/challenge page.
                    raise DatiNonDisponibili(
                        f"Tabella BTP non trovata a pagina {pagina}: probabile blocco del WAF, "
                        "la lista sarebbe incompleta"
                    )
            if pagina == 1 and len(tabella.find_all("tr")) < 2:
                    raise DatiNonDisponibili("La tabella BTP è vuota")

            strumenti = _estrai_strumenti(tabella, lingua)

            if len(strumenti) <= 0:
                pass
            nuovi = [s for s in strumenti if s.isin not in isin_visti]
            if not nuovi:
                # Empty page (past the end) or a page repeating the previous one.
                break
            risultati.extend(nuovi)
            isin_visti.update(s.isin for s in nuovi)
            print(f'Pagina {pagina} - {market_url}')
            if _ha_pagina_successiva(soup, pagina) is False:
                break

        return risultati

    finally:
        if sessione_locale:
            sessione.chiudi()
