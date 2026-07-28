"""
Unit Tests — Node 3: split.py
Tests: no entity overlap across splits, chronological order preserved, row-count sum equals total.
"""
import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Replicate split.py group-chronological split logic without AWS calls
# ---------------------------------------------------------------------------

def _chronological_split(df: pd.DataFrame, identifier: str):
    unique_ids = sorted(df[identifier].unique())
    n = len(unique_ids)
    train_end = int(n * 0.70)
    val_end   = int(n * 0.85)

    train_ids = unique_ids[:train_end]
    val_ids   = unique_ids[train_end:val_end]
    test_ids  = unique_ids[val_end:]

    train_df = df[df[identifier].isin(train_ids)].copy().reset_index(drop=True)
    val_df   = df[df[identifier].isin(val_ids)].copy().reset_index(drop=True)
    test_df  = df[df[identifier].isin(test_ids)].copy().reset_index(drop=True)

    return train_df, val_df, test_df


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

def _make_df(n_engines: int = 10, cycles_per_engine: int = 40) -> pd.DataFrame:
    np.random.seed(42)
    rows = []
    for eid in range(1, n_engines + 1):
        for c in range(1, cycles_per_engine + 1):
            rows.append({
                "global_engine_id": eid,
                "cycle": c,
                "RUL": cycles_per_engine - c,
                "sensor_2": float(np.random.normal(50, 5)),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSplit:

    def test_no_entity_overlap_train_val(self):
        df = _make_df()
        train, val, _ = _chronological_split(df, "global_engine_id")
        overlap = set(train["global_engine_id"]) & set(val["global_engine_id"])
        assert len(overlap) == 0, f"Entity overlap between train and val: {overlap}"

    def test_no_entity_overlap_train_test(self):
        df = _make_df()
        train, _, test = _chronological_split(df, "global_engine_id")
        overlap = set(train["global_engine_id"]) & set(test["global_engine_id"])
        assert len(overlap) == 0, f"Entity overlap between train and test: {overlap}"

    def test_no_entity_overlap_val_test(self):
        df = _make_df()
        _, val, test = _chronological_split(df, "global_engine_id")
        overlap = set(val["global_engine_id"]) & set(test["global_engine_id"])
        assert len(overlap) == 0, f"Entity overlap between val and test: {overlap}"

    def test_row_counts_sum_to_total(self):
        df = _make_df()
        train, val, test = _chronological_split(df, "global_engine_id")
        total = len(train) + len(val) + len(test)
        assert total == len(df), (
            f"Row sum {total} does not equal original {len(df)}"
        )

    def test_train_is_largest_split(self):
        df = _make_df()
        train, val, test = _chronological_split(df, "global_engine_id")
        assert len(train) > len(val), "Train should be larger than val"
        assert len(train) > len(test), "Train should be larger than test"

    def test_chronological_order_within_engine(self):
        df = _make_df()
        train, _, _ = _chronological_split(df, "global_engine_id")
        for eid, grp in train.groupby("global_engine_id"):
            cycles = grp["cycle"].tolist()
            assert cycles == sorted(cycles), (
                f"Cycles for engine {eid} are not in order: {cycles}"
            )

    def test_split_is_deterministic(self):
        df = _make_df()
        train1, val1, test1 = _chronological_split(df, "global_engine_id")
        train2, val2, test2 = _chronological_split(df, "global_engine_id")
        pd.testing.assert_frame_equal(train1, train2)
        pd.testing.assert_frame_equal(val1,   val2)
        pd.testing.assert_frame_equal(test1,  test2)

    def test_all_splits_nonempty(self):
        df = _make_df(n_engines=10)
        train, val, test = _chronological_split(df, "global_engine_id")
        assert len(train) > 0, "Train split is empty"
        assert len(val)   > 0, "Val split is empty"
        assert len(test)  > 0, "Test split is empty"
