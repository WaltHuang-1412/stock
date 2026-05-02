"""
settlement_checker.py 單元測試

測試目標：
  - count_trading_days(): 交易日計算（排除週末）
  - check_settlement(): success / fail / holding 判斷邏輯
"""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from settlement_checker import count_trading_days, check_settlement


# ─── count_trading_days ───────────────────────────────────────────────────────

class TestCountTradingDays:

    def test_same_day(self):
        # 同一天 → 0 天
        assert count_trading_days("2026-04-21", "2026-04-21") == 0

    def test_one_day(self):
        # 週一 → 週二：1 個交易日
        assert count_trading_days("2026-04-20", "2026-04-21") == 1

    def test_week_no_weekend(self):
        # 週一到週五：4 個交易日
        assert count_trading_days("2026-04-20", "2026-04-24") == 4

    def test_skip_weekend(self):
        # 週五到下週一：1 個交易日（跳過週末）
        assert count_trading_days("2026-04-24", "2026-04-27") == 1

    def test_two_weeks(self):
        # 2026-04-13 (Mon) to 2026-04-24 (Fri) = 10 交易日（不含假日）
        assert count_trading_days("2026-04-13", "2026-04-24") == 9

    def test_cross_weekend_5days(self):
        # 週三到下週三：5 個交易日（週四、週五、週一、週二、週三）
        assert count_trading_days("2026-04-22", "2026-04-29") == 5


# ─── check_settlement ─────────────────────────────────────────────────────────

def _make_holding(
    code="2330",
    name="台積電",
    recommend_date="2026-04-14",
    recommend_price=1000.0,
    target_price=1100.0,
    stop_loss_pct=-10,
    settlement_days=10,
):
    """建立 holding dict"""
    return {
        code: {
            "stock_code": code,
            "stock_name": name,
            "industry": "半導體",
            "recommend_date": recommend_date,
            "recommend_price": recommend_price,
            "target_price": target_price,
            "stop_loss": round(recommend_price * (1 + stop_loss_pct / 100), 2),
            "stop_loss_pct": stop_loss_pct,
            "settlement_days": settlement_days,
            "score": 85,
            "position": "15%",
        }
    }


class TestCheckSettlement:

    def test_success_when_above_target(self):
        holdings = _make_holding(recommend_price=1000.0, target_price=1100.0)
        with patch("settlement_checker.get_current_price", return_value=1100.0):
            results = check_settlement(holdings, "2026-04-21")
        assert results[0]["result"] == "success"
        assert "1100" in results[0]["reason"]

    def test_success_when_exactly_at_target(self):
        holdings = _make_holding(recommend_price=1000.0, target_price=1100.0)
        with patch("settlement_checker.get_current_price", return_value=1100.0):
            results = check_settlement(holdings, "2026-04-21")
        assert results[0]["result"] == "success"

    def test_fail_when_below_stop_loss(self):
        # 停損 = 1000 * 0.9 = 900
        holdings = _make_holding(recommend_price=1000.0, stop_loss_pct=-10)
        with patch("settlement_checker.get_current_price", return_value=899.0):
            results = check_settlement(holdings, "2026-04-21")
        assert results[0]["result"] == "fail"
        assert "停損" in results[0]["reason"]

    def test_fail_when_exactly_at_stop_loss(self):
        holdings = _make_holding(recommend_price=1000.0, stop_loss_pct=-10)
        with patch("settlement_checker.get_current_price", return_value=900.0):
            results = check_settlement(holdings, "2026-04-21")
        assert results[0]["result"] == "fail"

    def test_holding_when_between_stop_and_target(self):
        # 現價 1050，目標 1100，停損 900，未到期
        holdings = _make_holding(
            recommend_date="2026-04-21",  # 今天剛推薦
            recommend_price=1000.0,
            target_price=1100.0,
            stop_loss_pct=-10,
            settlement_days=10,
        )
        with patch("settlement_checker.get_current_price", return_value=1050.0):
            results = check_settlement(holdings, "2026-04-21")
        assert results[0]["result"] == "holding"
        assert "D0/10" in results[0]["reason"]

    def test_expired_above_recommend_price_is_success(self):
        # 推薦 D10+，現價高於推薦價 → success
        holdings = _make_holding(
            recommend_date="2026-04-07",  # 14 天前
            recommend_price=1000.0,
            target_price=1500.0,  # 目標很高，未達到
            stop_loss_pct=-10,
            settlement_days=10,
        )
        # 2026-04-07 到 2026-04-21 = 10 個交易日（Mon-Fri×2）
        with patch("settlement_checker.get_current_price", return_value=1010.0):
            results = check_settlement(holdings, "2026-04-21")
        assert results[0]["result"] == "success"
        assert "到期" in results[0]["reason"]

    def test_expired_below_recommend_price_is_fail(self):
        holdings = _make_holding(
            recommend_date="2026-04-07",
            recommend_price=1000.0,
            target_price=1500.0,
            stop_loss_pct=-10,
            settlement_days=10,
        )
        with patch("settlement_checker.get_current_price", return_value=990.0):  # 低於推薦價
            results = check_settlement(holdings, "2026-04-21")
        assert results[0]["result"] == "fail"

    def test_error_when_price_unavailable(self):
        holdings = _make_holding()
        with patch("settlement_checker.get_current_price", return_value=None):
            results = check_settlement(holdings, "2026-04-21")
        assert results[0]["result"] == "error"

    def test_stop_loss_recalculated_from_pct(self):
        # 即使 stop_loss 值錯誤，也應從 stop_loss_pct 重算
        holdings = _make_holding(recommend_price=1000.0, stop_loss_pct=-10)
        # 把 stop_loss 改成錯誤值
        holdings["2330"]["stop_loss"] = 9999.0  # 故意錯誤

        with patch("settlement_checker.get_current_price", return_value=910.0):
            results = check_settlement(holdings, "2026-04-21")
        # 910 > 正確停損 900，應該是 holding，不應觸發 stop_loss=9999 的 fail
        assert results[0]["result"] == "holding"

    def test_change_pct_calculated(self):
        holdings = _make_holding(recommend_price=1000.0)
        with patch("settlement_checker.get_current_price", return_value=1050.0):
            results = check_settlement(holdings, "2026-04-21")
        assert results[0]["change_pct"] == 5.0

    def test_multiple_holdings(self):
        holdings = {}
        holdings.update(_make_holding("2330", recommend_price=1000.0, target_price=1100.0))
        holdings.update(_make_holding("2303", name="聯電", recommend_price=50.0, target_price=60.0))

        prices = {"2330": 1100.0, "2303": 44.0}  # 2330 成功，2303 停損

        def price_fn(code):
            return prices.get(code)

        with patch("settlement_checker.get_current_price", side_effect=price_fn):
            results = check_settlement(holdings, "2026-04-21")

        result_map = {r["stock_code"]: r["result"] for r in results}
        assert result_map["2330"] == "success"
        assert result_map["2303"] == "fail"
