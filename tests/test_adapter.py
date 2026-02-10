"""Tests for CircleMudAdapter integration."""

import os

import pytest

from genos.adapters.circlemud.adapter import CircleMudAdapter
from genos.adapters.detector import detect_mud_type
from genos.uir.validator import validate_uir

TBAMUD_ROOT = "/home/genos/workspace/tbamud"


@pytest.mark.skipif(
    not os.path.exists(TBAMUD_ROOT),
    reason="tbaMUD source not available",
)
class TestCircleMudAdapter:
    def test_detect(self):
        adapter = CircleMudAdapter(TBAMUD_ROOT)
        assert adapter.detect() is True

    def test_detect_auto(self):
        adapter = detect_mud_type(TBAMUD_ROOT)
        assert adapter is not None
        assert isinstance(adapter, CircleMudAdapter)

    def test_analyze(self):
        adapter = CircleMudAdapter(TBAMUD_ROOT)
        report = adapter.analyze()
        assert report.mud_type == "CircleMUD/tbaMUD"
        assert report.room_count > 100
        assert report.item_count > 50
        assert report.mob_count > 50
        assert report.zone_count > 10

    def test_parse_full(self):
        adapter = CircleMudAdapter(TBAMUD_ROOT)
        uir = adapter.parse()

        assert uir.source_mud is not None
        assert uir.source_mud.codebase == "CircleMUD"

        # Should have substantial data
        assert len(uir.rooms) > 100
        assert len(uir.items) > 50
        assert len(uir.monsters) > 50
        assert len(uir.zones) > 10
        assert len(uir.triggers) > 0
        assert len(uir.character_classes) == 4

        # Stats should match
        assert uir.migration_stats.total_rooms == len(uir.rooms)
        assert uir.migration_stats.total_items == len(uir.items)

    def test_validate_parsed_uir(self):
        adapter = CircleMudAdapter(TBAMUD_ROOT)
        uir = adapter.parse()
        result = validate_uir(uir)
        # Should be valid (warnings are OK)
        assert result.valid is True

    def test_detect_wrong_dir(self):
        adapter = CircleMudAdapter("/tmp")
        assert adapter.detect() is False
