from src.odds import _parse_the_odds_api_payload


def test_odds_provider_keeps_shortest_decimal_price_per_team():
    payload = [
        {
            "bookmakers": [
                {
                    "title": "Book A",
                    "last_update": "2026-06-23T06:00:00Z",
                    "markets": [
                        {
                            "key": "outrights",
                            "outcomes": [
                                {"name": "Brazil", "price": 6.0},
                                {"name": "Japan", "price": 25.0},
                            ],
                        }
                    ],
                },
                {
                    "title": "Book B",
                    "last_update": "2026-06-23T06:05:00Z",
                    "markets": [
                        {
                            "key": "outrights",
                            "outcomes": [
                                {"name": "Brazil", "price": 5.5},
                            ],
                        }
                    ],
                },
            ]
        }
    ]

    odds = _parse_the_odds_api_payload(payload)

    assert odds["BRA"].decimal == 5.5
    assert odds["BRA"].bookmaker == "Book B"
    assert odds["JPN"].decimal == 25.0
