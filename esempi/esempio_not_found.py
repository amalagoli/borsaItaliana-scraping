"""Monitora schede NOT FOUND che sembrano esistere"""

import polars as pl

from borsa_italiana_scraping.mot_ricerca import (
    # DatiNonDisponibili,
    Sessione,
    # lista_btp,
    # ottieni_intraday,
    # ottieni_prezzo_corrente,
    # ottieni_scheda,
    # ottieni_storico,
    lista_cerca_opzioni,
)
from borsa_italiana_scraping.scheda import _parsa_data_scheda, ottieni_scheda
from borsa_italiana_scraping.etlx import lista_tlx_opzioni

bit_ses = Sessione()

pl_options = lista_cerca_opzioni(bit_ses)

ISIN_NEG = ("BE0000353624", "AT0000A1PEF7", "AT0000A2HLC4", "AT0000A2HLC4")
_parsa_data_scheda("20/06/30", "en")
scheda = ottieni_scheda(ISIN_NEG[3], lingua="en", sessione=bit_ses)
print(scheda.scadenza)

pl_tls_opts = lista_tlx_opzioni()
# datetime.date(2015, 7, 27)
