from appverbo.services.whatsapp import map_whatsapp_delivery_status, normalize_whatsapp_recipient


def test_normalize_whatsapp_recipient() -> None:
    assert normalize_whatsapp_recipient("+351 912-345-678") == "351912345678"
    assert normalize_whatsapp_recipient("00351912345678") == "351912345678"
    assert normalize_whatsapp_recipient("abc") == ""


def test_map_whatsapp_delivery_status() -> None:
    assert map_whatsapp_delivery_status("read") == "active"
    assert map_whatsapp_delivery_status("delivered") == "active"
    assert map_whatsapp_delivery_status("failed") == "invalid"
    assert map_whatsapp_delivery_status("unknown-status") == "pending"
