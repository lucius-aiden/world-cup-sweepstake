from __future__ import annotations

import unicodedata

ALIASES = {
    "ALGERIA": "ALG",
    "ARGENTINA": "ARG",
    "AUSTRALIA": "AUS",
    "AUSTRIA": "AUT",
    "BELGIUM": "BEL",
    "BOSNIAANDHERZEGOVINA": "BIH",
    "BRAZIL": "BRA",
    "CAPEVERDE": "CPV",
    "CAMEROON": "CMR",
    "CANADA": "CAN",
    "CHILE": "CHI",
    "COLOMBIA": "COL",
    "COSTARICA": "CRC",
    "CROATIA": "CRO",
    "CURACAO": "CUW",
    "CURAÇAO": "CUW",
    "CZECHREPUBLIC": "CZE",
    "DENMARK": "DEN",
    "DEMOCRATICREPUBLICOFTHECONGO": "COD",
    "DRCONGO": "COD",
    "ECUADOR": "ECU",
    "EGYPT": "EGY",
    "ENGLAND": "ENG",
    "FRANCE": "FRA",
    "GERMANY": "GER",
    "GHANA": "GHA",
    "HAITI": "HTI",
    "HAI": "HTI",
    "HTI": "HTI",
    "IRAN": "IRN",
    "IRAQ": "IRQ",
    "ITALY": "ITA",
    "JORDAN": "JOR",
    "IVORYCOAST": "CIV",
    "COTEDIVOIRE": "CIV",
    "JAPAN": "JPN",
    "KOREAREPUBLIC": "KOR",
    "KOREAREP": "KOR",
    "REPUBLICOFKOREA": "KOR",
    "ROK": "KOR",
    "SOUTHKOREA": "KOR",
    "MEXICO": "MEX",
    "MOROCCO": "MAR",
    "NETHERLANDS": "NED",
    "NEWZEALAND": "NZL",
    "NIGERIA": "NGA",
    "NORWAY": "NOR",
    "PANAMA": "PAN",
    "PARAGUAY": "PAR",
    "PERU": "PER",
    "POLAND": "POL",
    "PORTUGAL": "POR",
    "QATAR": "QAT",
    "SAUDIARABIA": "KSA",
    "SCOTLAND": "SCO",
    "SENEGAL": "SEN",
    "SERBIA": "SRB",
    "SOUTHAFRICA": "RSA",
    "SPAIN": "ESP",
    "SWEDEN": "SWE",
    "SWITZERLAND": "SUI",
    "TUNISIA": "TUN",
    "TURKIYE": "TUR",
    "TURKEY": "TUR",
    "UZBEKISTAN": "UZB",
    "UNITEDSTATES": "USA",
    "USA": "USA",
    "URUGUAY": "URU",
    "WALES": "WAL",
}


def canonical_team_key(team_name: str) -> str:
    normalized = unicodedata.normalize("NFKD", team_name)
    ascii_friendly = "".join(character for character in normalized if not unicodedata.combining(character))
    return "".join(character for character in ascii_friendly.upper() if character.isalnum())


def resolve_team_code(team_name: str, provider_code: str | None = None) -> str:
    if provider_code:
        cleaned = canonical_team_key(provider_code)
        if cleaned in ALIASES:
            return ALIASES[cleaned]
        if 2 <= len(cleaned) <= 4:
            return cleaned
    key = canonical_team_key(team_name)
    if key in ALIASES:
        return ALIASES[key]
    if len(key) <= 4:
        return key
    return key[:12]
