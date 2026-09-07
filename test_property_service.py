from property_service import aggregate_listings


def test_duplicate_address_keeps_cheapest_and_merges_reminders():
    rows = [
        {"source": "north", "address": "12 Cedar St", "rent": 2200, "maintenance_due": True},
        {"source": "south", "address": " 12   cedar st ", "rent": 2100, "inspection_due": True},
    ]
    result = aggregate_listings(rows)
    assert len(result) == 1
    assert result[0].rent == 2100
    assert result[0].maintenance_due is True
    assert result[0].inspection_due is True
