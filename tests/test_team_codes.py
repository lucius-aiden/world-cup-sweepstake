from src.team_codes import resolve_team_code


def test_provider_code_alias_maps_haiti_correctly():
    assert resolve_team_code("Haiti", "HAI") == "HTI"
    assert resolve_team_code("Haiti", "HTI") == "HTI"


def test_variant_names_and_codes_map_knockout_teams_correctly():
    assert resolve_team_code("Curaçao", None) == "CUW"
    assert resolve_team_code("Türkiye", None) == "TUR"
    assert resolve_team_code("Korea Rep.", None) == "KOR"
    assert resolve_team_code("Republic of Korea", None) == "KOR"
    assert resolve_team_code("South Korea", "ROK") == "KOR"
