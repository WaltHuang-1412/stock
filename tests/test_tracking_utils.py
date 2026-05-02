"""
tracking_utils.py 單元測試

測試目標：
  - validate_tracking(): 欄位缺失、型別錯誤、stop_loss 計算不符
  - recalculate_stop_losses(): 自動修正 stop_loss
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from tracking_utils import validate_tracking, recalculate_stop_losses


def _make_rec(**kwargs):
    """建立一個合法的推薦項目，可用 kwargs 覆蓋欄位"""
    base = {
        "stock_code": "2330",
        "stock_name": "台積電",
        "recommend_price": 1000.0,
        "target_price": 1100.0,
        "stop_loss_pct": -10,
        "settlement_days": 10,
        "stop_loss": 900.0,  # 1000 * 0.9
    }
    base.update(kwargs)
    return base


def _make_tracking(recs=None):
    return {
        "date": "2026-04-21",
        "recommendations": recs if recs is not None else [_make_rec()],
    }


# ─── validate_tracking ────────────────────────────────────────────────────────

class TestValidateTracking:

    def test_valid_passes(self):
        errors = validate_tracking(_make_tracking())
        assert errors == [], f"期望無錯誤，實際: {errors}"

    def test_root_not_dict(self):
        errors = validate_tracking([])
        assert any("dict" in e for e in errors)

    def test_missing_date(self):
        data = _make_tracking()
        del data["date"]
        errors = validate_tracking(data)
        assert any("date" in e for e in errors)

    def test_missing_recommendations(self):
        data = {"date": "2026-04-21"}
        errors = validate_tracking(data)
        assert any("recommendations" in e for e in errors)

    def test_missing_stock_code(self):
        rec = _make_rec()
        del rec["stock_code"]
        errors = validate_tracking(_make_tracking([rec]))
        assert any("stock_code" in e for e in errors)

    def test_missing_stop_loss_pct(self):
        rec = _make_rec()
        del rec["stop_loss_pct"]
        errors = validate_tracking(_make_tracking([rec]))
        assert any("stop_loss_pct" in e for e in errors)

    def test_missing_settlement_days(self):
        rec = _make_rec()
        del rec["settlement_days"]
        errors = validate_tracking(_make_tracking([rec]))
        assert any("settlement_days" in e for e in errors)

    def test_wrong_type_recommend_price(self):
        rec = _make_rec(recommend_price="1000")  # str 而非 float
        errors = validate_tracking(_make_tracking([rec]))
        assert any("recommend_price" in e for e in errors)

    def test_wrong_type_settlement_days(self):
        rec = _make_rec(settlement_days=10.0)  # float 而非 int
        errors = validate_tracking(_make_tracking([rec]))
        assert any("settlement_days" in e for e in errors)

    def test_zero_recommend_price(self):
        rec = _make_rec(recommend_price=0)
        errors = validate_tracking(_make_tracking([rec]))
        assert any("recommend_price" in e for e in errors)

    def test_negative_recommend_price(self):
        rec = _make_rec(recommend_price=-50.0)
        errors = validate_tracking(_make_tracking([rec]))
        assert any("recommend_price" in e for e in errors)

    def test_stop_loss_mismatch(self):
        # stop_loss_pct=-10 + recommend_price=1000 → 應是 900，但填 800
        rec = _make_rec(stop_loss=800.0)
        errors = validate_tracking(_make_tracking([rec]))
        assert any("stop_loss" in e for e in errors)

    def test_stop_loss_correct(self):
        # 1000 * (1 - 10/100) = 900
        rec = _make_rec(recommend_price=1000.0, stop_loss_pct=-10, stop_loss=900.0)
        errors = validate_tracking(_make_tracking([rec]))
        assert errors == []

    def test_stop_loss_tolerance(self):
        # 允許 0.1 元誤差
        rec = _make_rec(recommend_price=1000.0, stop_loss_pct=-10, stop_loss=900.05)
        errors = validate_tracking(_make_tracking([rec]))
        assert errors == []

    def test_multiple_recs_mixed_errors(self):
        good = _make_rec(stock_code="2330")
        bad = _make_rec(stock_code="2303")
        del bad["stop_loss_pct"]
        errors = validate_tracking(_make_tracking([good, bad]))
        # 只有 2303 出錯
        assert any("2303" in e for e in errors)
        assert not any("2330" in e for e in errors)

    def test_int_recommend_price_accepted(self):
        # int 也是合法的 (int, float) 型別
        rec = _make_rec(recommend_price=1000, stop_loss=900)
        errors = validate_tracking(_make_tracking([rec]))
        assert errors == []


# ─── recalculate_stop_losses ──────────────────────────────────────────────────

class TestRecalculateStopLosses:

    def test_correct_stop_loss_unchanged(self):
        data = _make_tracking([_make_rec(recommend_price=1000.0, stop_loss_pct=-10, stop_loss=900.0)])
        fixed = recalculate_stop_losses(data)
        assert fixed == []
        assert data["recommendations"][0]["stop_loss"] == 900.0

    def test_wrong_stop_loss_corrected(self):
        data = _make_tracking([_make_rec(recommend_price=1000.0, stop_loss_pct=-10, stop_loss=800.0)])
        fixed = recalculate_stop_losses(data)
        assert len(fixed) == 1
        assert fixed[0]["new"] == 900.0
        assert data["recommendations"][0]["stop_loss"] == 900.0

    def test_no_stop_loss_key_gets_set(self):
        rec = _make_rec(recommend_price=500.0, stop_loss_pct=-10)
        del rec["stop_loss"]  # 沒有 stop_loss 欄位
        data = _make_tracking([rec])
        fixed = recalculate_stop_losses(data)
        assert len(fixed) == 1
        assert data["recommendations"][0]["stop_loss"] == 450.0

    def test_multiple_recs_all_corrected(self):
        recs = [
            _make_rec(stock_code="2330", recommend_price=1000.0, stop_loss_pct=-10, stop_loss=999.0),
            _make_rec(stock_code="2303", recommend_price=50.0, stop_loss_pct=-10, stop_loss=999.0),
        ]
        data = _make_tracking(recs)
        fixed = recalculate_stop_losses(data)
        assert len(fixed) == 2
        assert data["recommendations"][0]["stop_loss"] == 900.0
        assert data["recommendations"][1]["stop_loss"] == 45.0

    def test_missing_recommend_price_skipped(self):
        rec = {"stock_code": "2330", "stock_name": "台積電", "stop_loss_pct": -10}
        data = _make_tracking([rec])
        fixed = recalculate_stop_losses(data)
        assert fixed == []

    def test_rounding_precision(self):
        # 推薦價 123.4, -5% → 117.23
        rec = _make_rec(recommend_price=123.4, stop_loss_pct=-5, stop_loss=999.0)
        data = _make_tracking([rec])
        recalculate_stop_losses(data)
        assert data["recommendations"][0]["stop_loss"] == round(123.4 * 0.95, 2)
