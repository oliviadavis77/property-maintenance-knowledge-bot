from src.property_knowledge_bot import MaintenanceRequest, triage


def test_tenant_safety_request_becomes_immediate() -> None:
    request = MaintenanceRequest("building-17", "lease-2026-04", "Water leak under kitchen sink", 3)

    result = triage(request)

    assert result.priority == "immediate"
    assert "protect" in result.reason


def test_inspection_deadline_becomes_immediate() -> None:
    request = MaintenanceRequest("building-17", "inspection-2026", "Replace hallway light", 1)

    assert triage(request).priority == "immediate"
