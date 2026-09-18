"""Pipeline orchestration tests."""

import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

import pipeline


def test_extraction_failure_does_not_mutate_warehouse():
    with (
        patch.object(pipeline, "get_contacts", return_value=[]),
        patch.object(pipeline, "get_deals", side_effect=RuntimeError("upstream unavailable")),
        patch.object(pipeline, "load") as loader,
    ):
        with pytest.raises(RuntimeError, match="upstream unavailable"):
            pipeline.run()

    loader.assert_not_called()


def test_pipeline_loads_only_after_all_extracts_succeed():
    with (
        patch.object(pipeline, "get_contacts", return_value=[{"id": "1", "properties": {}}]),
        patch.object(pipeline, "get_deals", return_value=[{"id": "2", "properties": {}}]),
        patch.object(pipeline, "get_companies", return_value=[{"id": "3", "properties": {}}]),
        patch.object(pipeline, "load") as loader,
    ):
        pipeline.run()

    assert [item.args[0] for item in loader.call_args_list] == ["contacts", "deals", "companies"]
