"""
check_market_status.py 單元測試

使用 mock 隔絕所有外部 API 呼叫，測試純邏輯。

測試目標：
  - _is_weekend(): 週末/週間判斷
  - is_tw_trading_day(): 優先順序（週末→未來→快取→T86→MIS→預設）
  - is_us_trading_day(): Yahoo Finance timestamp 比對
  - check_market_status(): full/snapshot/skip 狀態判斷
"""

import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import check_market_status as cms


# ─── _is_weekend ─────────────────────────────────────────────────────────────

class TestIsWeekend:

    def test_monday(self):
        assert cms._is_weekend("2026-04-27") is False  # Monday

    def test_friday(self):
        assert cms._is_weekend("2026-04-24") is False  # Friday

    def test_saturday(self):
        assert cms._is_weekend("2026-04-25") is True   # Saturday

    def test_sunday(self):
        assert cms._is_weekend("2026-04-26") is True   # Sunday


# ─── _check_twse_t86 ──────────────────────────────────────────────────────────

class TestCheckTwseT86:

    def _mock_response(self, data, status=200):
        resp = MagicMock()
        resp.status_code = status
        resp.json.return_value = data
        return resp

    def test_has_data_returns_true(self):
        with patch("check_market_status.requests.get") as mock_get:
            mock_get.return_value = self._mock_response({"data": [["2330", "台積電"]]})
            result = cms._check_twse_t86("20260421")
        assert result is True

    def test_empty_data_returns_false(self):
        with patch("check_market_status.requests.get") as mock_get:
            mock_get.return_value = self._mock_response({"data": []})
            result = cms._check_twse_t86("20260501")  # 例假日
        assert result is False

    def test_no_data_key_returns_false(self):
        with patch("check_market_status.requests.get") as mock_get:
            mock_get.return_value = self._mock_response({"stat": "no data"})
            result = cms._check_twse_t86("20260501")
        assert result is False

    def test_network_error_returns_none(self):
        with patch("check_market_status.requests.get", side_effect=Exception("timeout")):
            result = cms._check_twse_t86("20260421")
        assert result is None


# ─── _check_twse_mis ─────────────────────────────────────────────────────────

class TestCheckTwseMis:

    def _mock_response(self, data, status=200):
        resp = MagicMock()
        resp.status_code = status
        resp.json.return_value = data
        return resp

    def test_matching_date_with_price_returns_true(self):
        with patch("check_market_status.requests.get") as mock_get:
            mock_get.return_value = self._mock_response({
                "msgArray": [{"d": "20260421", "z": "1000"}]
            })
            result = cms._check_twse_mis("2026-04-21")
        assert result is True

    def test_matching_date_no_price_returns_true(self):
        # z='-' 表示盤前未成交，但日期吻合仍視為開市
        with patch("check_market_status.requests.get") as mock_get:
            mock_get.return_value = self._mock_response({
                "msgArray": [{"d": "20260421", "z": "-"}]
            })
            result = cms._check_twse_mis("2026-04-21")
        assert result is True

    def test_date_mismatch_returns_false(self):
        # MIS 顯示的是上個交易日，今天是假日
        with patch("check_market_status.requests.get") as mock_get:
            mock_get.return_value = self._mock_response({
                "msgArray": [{"d": "20260420", "z": "1000"}]
            })
            result = cms._check_twse_mis("2026-04-21")  # 查 21 但 MIS 回傳 20
        assert result is False

    def test_network_error_returns_none(self):
        with patch("check_market_status.requests.get", side_effect=Exception("conn failed")):
            result = cms._check_twse_mis("2026-04-21")
        assert result is None


# ─── is_tw_trading_day ────────────────────────────────────────────────────────

class TestIsTwTradingDay:

    def test_saturday_returns_false(self):
        result = cms.is_tw_trading_day("2026-04-25")
        assert result is False

    def test_sunday_returns_false(self):
        result = cms.is_tw_trading_day("2026-04-26")
        assert result is False

    def test_future_weekday_returns_true(self):
        # 未來日期不查 API，直接返回 True
        result = cms.is_tw_trading_day("2099-01-01")
        assert result is True

    def test_cache_hit_returns_true(self):
        # 本地快取存在 → 直接 True，不查 API
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            cache_file = cache_dir / "twse_t86_20260421.json"
            cache_file.write_text("{}")  # 建立快取

            with patch.object(cms, "CACHE_DIR", cache_dir):
                result = cms.is_tw_trading_day("2026-04-21")
        assert result is True

    def test_t86_says_open(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(cms, "CACHE_DIR", Path(tmpdir)):
                with patch("check_market_status._check_twse_t86", return_value=True):
                    result = cms.is_tw_trading_day("2026-04-21")
        assert result is True

    def test_t86_says_holiday(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(cms, "CACHE_DIR", Path(tmpdir)):
                with patch("check_market_status._check_twse_t86", return_value=False):
                    result = cms.is_tw_trading_day("2026-05-01")
        assert result is False

    def test_t86_fails_falls_back_to_mis(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(cms, "CACHE_DIR", Path(tmpdir)):
                with patch("check_market_status._check_twse_t86", return_value=None):
                    with patch("check_market_status._check_twse_mis", return_value=True):
                        result = cms.is_tw_trading_day("2026-04-21")
        assert result is True

    def test_both_fail_defaults_to_true(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(cms, "CACHE_DIR", Path(tmpdir)):
                with patch("check_market_status._check_twse_t86", return_value=None):
                    with patch("check_market_status._check_twse_mis", return_value=None):
                        result = cms.is_tw_trading_day("2026-04-21")
        assert result is True


# ─── is_us_trading_day ────────────────────────────────────────────────────────

class TestIsUsTradingDay:

    def test_weekend_returns_false(self):
        result = cms.is_us_trading_day("2026-04-25")
        assert result is False

    def test_us_holiday_returns_false(self):
        # timestamp 不含目標日期 → 休市
        with patch("check_market_status.requests.get") as mock_get:
            resp = MagicMock()
            resp.status_code = 200
            # 回傳一個不包含目標日期的 timestamp（美股休市）
            from datetime import datetime, timezone
            prev_day_ts = int(datetime(2026, 7, 2, 13, 30).timestamp())  # 前一天
            resp.json.return_value = {
                "chart": {"result": [{"timestamp": [prev_day_ts]}]}
            }
            mock_get.return_value = resp
            result = cms.is_us_trading_day("2026-07-04")  # 美國獨立紀念日
        assert result is False

    def test_us_trading_day_returns_true(self):
        from datetime import datetime
        target = datetime(2026, 4, 21, 13, 30)  # EDT 13:30
        with patch("check_market_status.requests.get") as mock_get:
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = {
                "chart": {"result": [{"timestamp": [int(target.timestamp())]}]}
            }
            mock_get.return_value = resp
            result = cms.is_us_trading_day("2026-04-21")
        assert result is True

    def test_api_fail_defaults_to_true(self):
        with patch("check_market_status.requests.get", side_effect=Exception("timeout")):
            result = cms.is_us_trading_day("2026-04-21")
        assert result is True


# ─── check_market_status ─────────────────────────────────────────────────────

class TestCheckMarketStatus:

    def test_tw_open_returns_full(self):
        with patch("check_market_status.is_tw_trading_day", return_value=True):
            result = cms.check_market_status("2026-04-21", "before_market")
        assert result == "full"

    def test_tw_holiday_intraday_returns_skip(self):
        with patch("check_market_status.is_tw_trading_day", return_value=False):
            result = cms.check_market_status("2026-05-01", "intraday")
        assert result == "skip"

    def test_tw_holiday_after_market_returns_skip(self):
        with patch("check_market_status.is_tw_trading_day", return_value=False):
            result = cms.check_market_status("2026-05-01", "after_market")
        assert result == "skip"

    def test_tw_holiday_us_open_returns_snapshot(self):
        with patch("check_market_status.is_tw_trading_day", return_value=False):
            with patch("check_market_status.find_previous_tw_trading_day", return_value="2026-04-30"):
                with patch("check_market_status.has_us_trading_days_since", return_value=True):
                    result = cms.check_market_status("2026-05-01", "before_market")
        assert result == "snapshot"

    def test_tw_holiday_us_also_closed_returns_skip(self):
        with patch("check_market_status.is_tw_trading_day", return_value=False):
            with patch("check_market_status.find_previous_tw_trading_day", return_value="2026-04-30"):
                with patch("check_market_status.has_us_trading_days_since", return_value=False):
                    result = cms.check_market_status("2026-05-01", "before_market")
        assert result == "skip"

    def test_cannot_find_prev_tw_day_returns_skip(self):
        with patch("check_market_status.is_tw_trading_day", return_value=False):
            with patch("check_market_status.find_previous_tw_trading_day", return_value=None):
                result = cms.check_market_status("2026-05-01", "before_market")
        assert result == "skip"

    def test_labor_day_5_1_is_tw_holiday(self):
        # 勞動節 5/1 是台灣國定假日
        # 透過 mock T86 回傳空資料（假日無資料）
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(cms, "CACHE_DIR", Path(tmpdir)):
                with patch("check_market_status._check_twse_t86", return_value=False):
                    result = cms.is_tw_trading_day("2026-05-01")
        assert result is False
