""" Utilities to manage Polars intereaction """
from __future__ import annotations

from dataclasses import asdict, fields # , dataclass, fields

import polars as pl

# from .eccezioni import DatiNonDisponibili
from .tipi import SchedaStrumento, StrumentoLista

_STR_TO_PL_TYPES = {
        "str": pl.String,
        "Decimal": pl.Float64,
        "int": pl.Int64,
        "date": pl.Date,
        "list": pl.List
    }


def lista_to_pl(lista: StrumentoLista | list[StrumentoLista]) -> pl.Dataframe:
    """Converti struttura StrumentLista a Polars dataframe"""
    # Map types
    # schema_ = {
    #     "isin": pl.String,
    #     "nome": pl.String,
    #     "ultimo_prezzo": pl.Float64,
    #     "cedola": pl.Float64,
    #     "scadenza": pl.Date,
    #     "mic": pl.String,
    # }
    # pl_list =  pl.DataFrame(
    #     {
    #         "isin": lista.isin,
    #         "nome": lista.nome,
    #         "ultimo_prezzo": lista.ultimo_prezzo,
    #         "cedola": lista.cedola,
    #         "scadenza": lista.scadenza,
    #         "mic": lista.mic,
    #     },
    #     schema=schema_,
    # )

    if isinstance(lista, list):
        pl_list = pl.concat([lista_to_pl(l) for l in lista])
    else:
        ff = fields(lista )
        cnames = [f.name for f in ff]
        types = [f.type for f in ff]
        valid_types = list(_STR_TO_PL_TYPES.keys())
        type_loc = [t for tt in [[i for i, tt in enumerate(valid_types) if t.find(tt) >= 0] for t in types] for t in tt]
        pl_types = [_STR_TO_PL_TYPES[valid_types[i]] for i in type_loc]
        pl_schema = dict(zip(cnames, pl_types))
        pl_list = pl.DataFrame(asdict(lista), schema=pl_schema)
    return pl_list

def scheda_to_pl(scheda: SchedaStrumento | list):
    """ Converti struttura SchedaStrumento a Polars dataframe """
    if isinstance(scheda, list):
        pl_list = pl.concat([lista_to_pl(l) for l in scheda])
    else:
        ff = fields(scheda)
        cnames = [f.name for f in ff]
        types = [f.type for f in ff]
        valid_types = list(_STR_TO_PL_TYPES.keys())
        type_loc = [t for tt in [[i for i, tt in enumerate(valid_types) if t.find(tt) >= 0] for t in types] for t in tt]
        pl_types = [_STR_TO_PL_TYPES[valid_types[i]] for i in type_loc]
        pl_schema = dict(zip(cnames, pl_types))
        pl_scheda = pl.DataFrame(asdict(scheda), schema=pl_schema)
    return pl_scheda
