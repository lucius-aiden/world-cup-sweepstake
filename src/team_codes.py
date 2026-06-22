from __future__ import annotations

ALIASES = {
    "ARGENTINA": "ARG",
    "AUSTRALIA": "AUS",
    "AUSTRIA": "AUT",
    "BELGIUM": "BEL",
    "BRAZIL": "BRA",
    "CAMEROON": "CMR",
    "CANADA": "CAN",
    "CHILE": "CHI",
    "COLOMBIA": "COL",
    "COSTARICA": "CRC",
    "CROATIA": "CRO",
    "DENMARK": "DEN",
    "ECUADOR": "ECU",
    "EGYPT": "EGY",
    "ENGLAND": "ENG",
    "FRANCE": "FRA",
    "GERMANY": "GER",
    "GHANA": "GHA",
    "IRAN": "IRN",
    "ITALY": "ITA",
    "IVORYCOAST": "CIV",
    "COTEDIVOIRE": "CIV",
    "JAPAN": "JPN",
    "KOREAREPUBLIC": "KOR",
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
    "SENEGAL": "SEN",
    "SERBIA": "SRB",
    "SPAIN": "ESP",
    "SWEDEN": "SWE",
    "SWITZERLAND": "SUI",
    "TUNISIA": "TUN",
    "TURKIYE": "TUR",
    "TURKEY": "TUR",
    "UNITEDSTATES": "USA",
    "USA": "USA",
    "URUGUAY": "URU",
    "WALES": "WAL",
}


def canonical_team_key(team_name: str) -> str:
    return "".join(character for character in team_name.upper() if character.isalnum())


def resolve_team_code(team_name: str, provider_code: str | None = None) -> str:
    if provider_code:
        cleaned = canonical_team_key(provider_code)
        if 2 <= len(cleaned) <= 4:
            return cleaned
    key = canonical_team_key(team_name)
    if key in ALIASES:
        return ALIASES[key]
    if len(key) <= 4:
        return key
    return key[:12]

