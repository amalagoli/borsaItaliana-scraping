"""Scraping delle liste strumenti (BTP, BOT, ecc.) da Borsa Italiana."""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import polars as pl
from bs4 import BeautifulSoup

from .eccezioni import DatiNonDisponibili
from .sessione import Sessione
from .tipi import StrumentoLista

# URL lista BTP
_URL_LISTA_BTP = "https://www.borsaitaliana.it/borsa/obbligazioni/mot/btp/lista.html"
_URL_LISTA_MOT = "https://www.borsaitaliana.it/borsa/obbligazioni/mot/{mercato_}/lista.html"

_MOT_MARKETS = {
    "Domestic": "obbligazioni-euro",
    "Euro": "euro-obbligazioni",
    "Bot": "bot",
    "Btp": "btp",
}


def _pulisci(testo: str) -> str:
    """Rimuove spazi extra e newline."""
    return " ".join(testo.split()).strip()


def _parsa_numero_lista(testo: str, lingua: str = "en") -> Decimal | None:
    """Converte una stringa numerica nella lista in Decimal."""
    testo = _pulisci(testo)
    if not testo or testo in ("-", "--", "n.a.", "N/A"):
        return None
    try:
        if lingua == "it":
            testo = testo.replace(".", "").replace(",", ".")
        else:
            testo = testo.replace(",", "")
        return Decimal(testo)
    except (InvalidOperation, ValueError):
        return None


def _parsa_data_lista(testo: str, lingua: str = "en") -> date | None:
    """Parsa una data dalla tabella lista."""
    testo = _pulisci(testo)
    if not testo or testo == "-":
        return None
    # ("%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d", "%d/%m/%y", "%Y/%m/%d")
    if lingua == "en":
        use_formats = ("%Y/%m/%d", "%y/%m/%d")
    else:
        use_formats = ("%d/%m/%Y", "%d/%m/%y")
    for fmt in use_formats:
        try:
            val_date = datetime.strptime(testo, fmt).date()
            # When the dateform is with two-digit years, there is a problem with verylong dated expirations
            if val_date.year < datetime.now().year:
                val_date = val_date.replace(year=val_date.year + 100)
            return val_date
        except ValueError:
            continue
    return None


def _estrai_isin_da_link(cella: BeautifulSoup) -> str | None:
    """Estrae l'ISIN da un link nella cella della tabella.

    L'ISIN ha formato: 2 lettere paese + 9 alfanumerici + 1 check digit.
    Usiamo un pattern più restrittivo per evitare falsi positivi
    (es. "OBBLIGAZIONI" che ha 12 lettere maiuscole).
    """
    # Pattern ISIN: esattamente 2 lettere + 10 tra cui almeno 1 cifra, con word boundary
    isin_re = re.compile(r"\b([A-Z]{2}[A-Z0-9]{9}[0-9])\b")

    link = cella.find("a")
    if link:
        href = str(link.get("href", "")).upper()
        match = isin_re.search(href)
        if match:
            return match.group(1)
    # Fallback: tutti i link nella cella
    for link in cella.find_all("a"):
        href = str(link.get("href", "")).upper()
        match = isin_re.search(href)
        if match:
            return match.group(1)
    # Fallback: testo della cella
    testo = _pulisci(cella.get_text()).upper()
    match = isin_re.search(testo)
    if match:
        return match.group(1)
    return None


def _estrai_mic_da_link(cella: BeautifulSoup) -> str:
    """Estrae il MIC dal link nella cella (es. IT0005634800-MOTX.html)."""
    for link in cella.find_all("a"):
        href = str(link.get("href", ""))
        match = re.search(r"-([A-Z]{4})\.html", href.upper())
        if match:
            return match.group(1)
    return "MOTX"


def _strumento_to_polars(lista: StrumentoLista) -> pl.Dataframe:
    """Converti struttura StrumentLista a Polars dataframe"""
    schema_ = {
        "isin": pl.String,
        "nome": pl.String,
        "ultimo_prezzo": pl.Float64,
        "cedola": pl.Float64,
        "scadenza": pl.Date,
        "mic": pl.String,
    }
    return pl.DataFrame(
        {
            "isin": lista.isin,
            "nome": lista.nome,
            "ultimo_prezzo": lista.ultimo_prezzo,
            "cedola": lista.cedola,
            "scadenza": lista.scadenza,
            "mic": lista.mic,
        },
        schema=schema_,
    )


def lista_btp(
    lingua: str = "en",
    sessione: Sessione | None = None,
) -> list[StrumentoLista]:
    """Ottiene la lista completa dei BTP quotati sul MOT.

    Esegue lo scraping della pagina HTML con la tabella di tutti i BTP.

    Args:
        lingua: ``"en"`` o ``"it"``.
        sessione: sessione HTTP riutilizzabile.

    Returns:
        Lista di ``StrumentoLista``, uno per ogni BTP.
    """
    lingua = lingua.lower()
    sessione_locale = sessione is None
    if sessione_locale:
        sessione = Sessione()

    try:
        soup = sessione.get_html(_URL_LISTA_BTP, params={"lang": lingua})

        # Cerca la tabella principale
        tabella = soup.find("table")
        if not tabella:
            raise DatiNonDisponibili("Tabella BTP non trovata nella pagina")

        righe = tabella.find_all("tr")
        if len(righe) < 2:
            raise DatiNonDisponibili("La tabella BTP è vuota")

        risultati: list[StrumentoLista] = []

        # Identifica la riga header (la prima con <th>)
        header = None
        header_idx = 0
        for i, riga in enumerate(righe):
            if riga.find("th"):
                header = riga
                header_idx = i
                break

        intestazioni: list[str] = []
        if header:
            intestazioni = [_pulisci(th.get_text()).lower() for th in header.find_all("th")]

        # Mappa colonne (flessibile per EN e IT)
        idx_nome: int | None = None
        idx_isin: int | None = None
        idx_prezzo: int | None = None
        idx_cedola: int | None = None
        idx_scadenza: int | None = None

        for i, h in enumerate(intestazioni):
            if any(k in h for k in ("name", "nome", "title", "titolo", "description", "descrizione")):
                idx_nome = i
            elif "isin" in h or "code" in h or "codice" in h:
                idx_isin = i
            elif "last" in h or "ultimo" in h or "price" in h or "prezzo" in h:
                idx_prezzo = i
            elif "coupon" in h or "cedola" in h:
                idx_cedola = i
            elif "expiry" in h or "scadenza" in h or "maturity" in h:
                idx_scadenza = i

        for riga in righe[header_idx + 1 :]:
            celle = riga.find_all("td")
            if not celle:
                continue

            # ISIN: prova dalla colonna dedicata, oppure dal primo link
            isin: str | None = None
            if idx_isin is not None and idx_isin < len(celle):
                isin = _estrai_isin_da_link(celle[idx_isin])
            if not isin:
                # Prova dal primo link nella riga
                isin = _estrai_isin_da_link(riga)
            if not isin:
                continue

            # MIC dal link
            mic = _estrai_mic_da_link(riga)

            # Nome
            nome = ""
            if idx_nome is not None and idx_nome < len(celle):
                nome = _pulisci(celle[idx_nome].get_text())
            if not nome:
                # Prova il testo del primo link
                link = riga.find("a")
                if link:
                    nome = _pulisci(link.get_text())
                if not nome:
                    nome = isin

            # Prezzo
            prezzo: Decimal | None = None
            if idx_prezzo is not None and idx_prezzo < len(celle):
                prezzo = _parsa_numero_lista(celle[idx_prezzo].get_text(), lingua)

            # Cedola
            cedola: Decimal | None = None
            if idx_cedola is not None and idx_cedola < len(celle):
                cedola = _parsa_numero_lista(celle[idx_cedola].get_text(), lingua)

            # Scadenza
            scadenza: date | None = None
            if idx_scadenza is not None and idx_scadenza < len(celle):
                scadenza = _parsa_data_lista(celle[idx_scadenza].get_text(), lingua)

            risultati.append(
                StrumentoLista(
                    isin=isin,
                    nome=nome,
                    ultimo_prezzo=prezzo,
                    cedola=cedola,
                    scadenza=scadenza,
                    mic=mic,
                )
            )

        return risultati

    finally:
        if sessione_locale:
            sessione.chiudi()


def leggi_lista_pagina(
    mercato: str | None,
    pagina: str | None = None,
    lingua: str = "en",
    sessione: Sessione | None = None,
) -> list[StrumentoLista]:
    """Ottiene la lista da una pagina di obbligazioni quotate sul MOT.

    Esegue lo scraping di una pagina HTML con la tabella di obbligazioni.

    Args:
        lingua: ``"en"`` o ``"it"``.
        sessione: sessione HTTP riutilizzabile.

    Returns:
        Lista di ``StrumentoLista``, uno per ogni BTP.
    """
    lingua = lingua.lower()
    sessione_locale = sessione is None
    if sessione_locale:
        sessione = Sessione()

    page_url = mercato  # _URL_LISTA_MOT.format(mercato_=mercato)
    if pagina is None:
        params_url = {"lang": lingua}
    else:
        params_url = {"page": pagina, "lang": lingua}

    try:
        soup = sessione.get_html(page_url)  # , params=params_url)

        # Cerca la tabella principale
        tabella = soup.find("table")
        if not tabella:
            raise DatiNonDisponibili("Tabella BTP non trovata nella pagina")

        righe = tabella.find_all("tr")
        if len(righe) < 2:
            raise DatiNonDisponibili("La tabella BTP è vuota")

        # risultati: list[StrumentoLista] = []
        risultati: list[pl.DataFrame] = []

        # Identifica la riga header (la prima con <th>)
        header = None
        header_idx = 0
        for i, riga in enumerate(righe):
            if riga.find("th"):
                header = riga
                header_idx = i
                break

        intestazioni: list[str] = []
        if header:
            intestazioni = [_pulisci(th.get_text()).lower() for th in header.find_all("th")]

        # Mappa colonne (flessibile per EN e IT)
        idx_nome: int | None = None
        idx_isin: int | None = None
        idx_prezzo: int | None = None
        idx_cedola: int | None = None
        idx_scadenza: int | None = None

        for i, h in enumerate(intestazioni):
            if any(k in h for k in ("name", "nome", "title", "titolo", "description", "descrizione")):
                idx_nome = i
            elif "isin" in h or "code" in h or "codice" in h:
                idx_isin = i
            elif "last" in h or "ultimo" in h or "price" in h or "prezzo" in h:
                idx_prezzo = i
            elif "coupon" in h or "cedola" in h:
                idx_cedola = i
            elif "expiry" in h or "scadenza" in h or "maturity" in h:
                idx_scadenza = i

        for riga in righe[header_idx + 1 :]:
            celle = riga.find_all("td")
            if not celle:
                continue

            # ISIN: prova dalla colonna dedicata, oppure dal primo link
            isin: str | None = None
            if idx_isin is not None and idx_isin < len(celle):
                isin = _estrai_isin_da_link(celle[idx_isin])
            if not isin:
                # Prova dal primo link nella riga
                isin = _estrai_isin_da_link(riga)
            if not isin:
                continue

            # MIC dal link
            mic = _estrai_mic_da_link(riga)

            # Nome
            nome = ""
            if idx_nome is not None and idx_nome < len(celle):
                nome = _pulisci(celle[idx_nome].get_text())
            if not nome:
                # Prova il testo del primo link
                link = riga.find("a")
                if link:
                    nome = _pulisci(link.get_text())
                if not nome:
                    nome = isin

            # Prezzo
            prezzo: Decimal | None = None
            if idx_prezzo is not None and idx_prezzo < len(celle):
                prezzo = _parsa_numero_lista(celle[idx_prezzo].get_text(), lingua)

            # Cedola
            cedola: Decimal | None = None
            if idx_cedola is not None and idx_cedola < len(celle):
                cedola = _parsa_numero_lista(celle[idx_cedola].get_text(), lingua)

            # Scadenza
            scadenza: date | None = None
            if idx_scadenza is not None and idx_scadenza < len(celle):
                scadenza = _parsa_data_lista(celle[idx_scadenza].get_text(), lingua)

            risultati.append(
                # _strumento_to_polars(
                StrumentoLista(
                    isin=isin,
                    nome=nome,
                    ultimo_prezzo=prezzo,
                    cedola=cedola,
                    scadenza=scadenza,
                    mic=mic,
                )
                # )
            )
        return risultati
    finally:
        if sessione_locale:
            sessione.chiudi()
