"""
test_scout_integration.py - Integration Tests for ScoutAgent 3-Method API and Compiler Fallback
=============================================================================================
Verifies:
  1. ScoutAgent 3-method lightweight API: inspect(), advise_strategy(), self_heal()
  2. UnifiedCompiler deterministic mode when scout=None
  3. UnifiedCompiler scout-assisted mode when scout is provided
  4. UnifiedCompiler triggering scout.self_heal() on compilation failure
"""

import zipfile
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

from aiconnex_zip_compiler.compiler import UnifiedCompiler
from aiconnex_zip_compiler.scout import ScoutAgent
from aiconnex_zip_compiler.plugins import PluginRegistry
from aiconnex_zip_compiler.intelligence.models import IntelligenceReport


@pytest.fixture(autouse=True)
def reset_registry():
    """Reset singleton registry before each test."""
    PluginRegistry.reset_instance()
    yield
    PluginRegistry.reset_instance()


@pytest.fixture
def synthetic_zip(tmp_path) -> Path:
    """Create a synthetic multi-table ZIP."""
    fact_df = pd.DataFrame({
        "DATE_TIME": ["2020-05-15 00:00:00", "2020-05-15 00:15:00"],
        "PLANT_ID": [101, 101],
        "POWER": [100.0, 105.0],
    })
    fact_csv = tmp_path / "Fact_Data.csv"
    fact_df.to_csv(fact_csv, index=False)

    zip_path = tmp_path / "test_data.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(fact_csv, arcname="Fact_Data.csv")

    return zip_path


def test_scout_agent_lightweight_api(synthetic_zip):
    """Test that ScoutAgent cleanly exposes inspect(), advise_strategy(), and self_heal()."""
    scout = ScoutAgent()

    # 1. inspect()
    report = scout.inspect(inventory=synthetic_zip, readme_text="Sample dataset readme")
    assert isinstance(report, IntelligenceReport)
    assert report.archive_name == synthetic_zip.name

    # 2. advise_strategy()
    df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
    tables = {"table1": df, "table2": df}
    strategy = scout.advise_strategy(tables=tables, inventory=[synthetic_zip])
    assert isinstance(strategy, str)
    assert strategy in ["vertical_stack", "per_partition_batch", "key_join", "single_merged"]

    # 3. self_heal()
    healed = scout.self_heal(error_traceback="Traceback (most recent call last):\nDummyError: Failed to parse", sample_bytes=b"dummy bytes")
    assert isinstance(healed, bool)


def test_compiler_deterministic_mode_scout_none(synthetic_zip, tmp_path):
    """Test compiler executes 100% deterministically when scout=None."""
    output_dir = tmp_path / "out_deterministic"
    compiler = UnifiedCompiler(zip_path=synthetic_zip, output_dir=output_dir, scout=None, batch=True)
    
    assert compiler.scout is None
    result = compiler.compile()

    assert result.success is True
    assert len(result.merged_files) > 0
    assert output_dir.joinpath("compiler_lock.json").exists()


def test_compiler_scout_assisted_mode(synthetic_zip, tmp_path):
    """Test compiler invokes scout.inspect() and scout.advise_strategy() when scout is provided."""
    output_dir = tmp_path / "out_scout_assisted"
    scout = ScoutAgent()
    
    # Spy / mock scout methods
    scout.inspect = MagicMock(side_effect=scout.inspect)
    scout.advise_strategy = MagicMock(side_effect=scout.advise_strategy)

    compiler = UnifiedCompiler(zip_path=synthetic_zip, output_dir=output_dir, scout=scout, batch=True)
    assert compiler.scout is scout

    result = compiler.compile()

    assert result.success is True
    assert scout.inspect.called
    assert scout.advise_strategy.called


def test_compiler_scout_self_heal_on_failure(tmp_path):
    """Test compiler invokes scout.self_heal() when compilation fails."""
    bad_zip = tmp_path / "invalid.zip"
    bad_zip.write_bytes(b"not a zip file content")

    output_dir = tmp_path / "out_failure"
    scout = ScoutAgent()
    scout.self_heal = MagicMock(return_value=False)

    compiler = UnifiedCompiler(zip_path=bad_zip, output_dir=output_dir, scout=scout, batch=True)
    result = compiler.compile()

    assert result.success is False
    assert scout.self_heal.called
