"""Monitora schede NOT FOUND che sembrano esistere"""

from borsa_italiana_scraping.scheda import _parsa_data_scheda, ottieni_scheda
from borsa_italiana_scraping.sessione import Sessione

NOT_FOUND = (
    "IT0005695553",
    "BE0000340498",
    "EU000A1G0DT0",
    "EU000A2SCAE8",
    "FR0013154044",
    "FR0013404969",
    "FR0014001NN8",
    "GR0124040743",
    "GR0124041758",
    "GR0124042764",
    "GR0128015725",
    "HU0000404165",
    "HU0000404892",
    "NZIBDDT019C1",
    "PTOTEAOE0005",
    "SE0007125927",
    "US298785HM16",
    "US298785KE52",
    "XS1107718279",
    "XS1347679448",
    "XS1515372271",
    "XS2740429076",
    "XS2840132802",
    "XS3275404591",
    "XS2856144576",
    "XS3384597699",
    "XS3362255237",
    "XS3384598820",
    "XS3040316971",
    "XS3384605625",
    "IT0005568347",
    "IT0005568404",
    "IT0005480980",
    "XS3238398245",
    "XS2856144576",
    "XS2740429076",
    "XS2840132802",
    "XS2406749478",
)

_parsa_data_scheda("15/07/27", lingua="it")

bit_ses = Sessione()
scheda = ottieni_scheda("AT0000383864", sessione=bit_ses)
scheda.scadenza
# datetime.date(2015, 7, 27)
