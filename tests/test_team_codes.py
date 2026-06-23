from src.team_codes import resolve_team_code


def test_provider_code_alias_maps_haiti_correctly():
    assert resolve_team_code("Haiti", "HAI") == "HTI"
    assert resolve_team_code("Haiti", "HTI") == "HTI"
