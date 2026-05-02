"""
yahoo_finance_api.py 單元測試

使用 mock 測試 .TW / .TWO 自動 fallback 邏輯，不依賴外部 API。

測試目標：
  - _fetch_chart(): .TW 成功 / .TW 失敗→.TWO / 兩者都失敗
  - get_current_price(): 正確回傳 regularMarketPrice
  - get_previous_close(): 從 meta 或 indicators 回傳
  - get_5day_change(): 計算正確
  - get_history(): 回傳結構完整
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import yahoo_finance_api as yf


# ─── helpers ────────────────────────────────────────────────────────────────

def _make_chart_result(price=1000.0, prev_close=950.0, closes=None, volumes=None):
    """建立一個模擬的 Yahoo Finance chart result"""
    closes = closes or [900.0, 920.0, 950.0, 980.0, 1000.0]
    volumes = volumes or [10000, 12000, 11000, 13000, 15000]
    return {
        "meta": {
            "regularMarketPrice": price,
            "previousClose": prev_close,
        },
        "timestamp": list(range(len(closes))),
        "indicators": {
            "quote": [{
                "open": closes,
                "high": [c + 10 for c in closes],
                "low": [c - 10 for c in closes],
                "close": closes,
                "volume": volumes,
            }]
        }
    }


def _mock_response_ok(price=1000.0, prev_close=950.0, closes=None):
    resp = MagicMock()
    resp.json.return_value = {
        "chart": {
            "result": [_make_chart_result(price=price, prev_close=prev_close, closes=closes)]
        }
    }
    return resp


def _mock_response_empty():
    resp = MagicMock()
    resp.json.return_value = {"chart": {"result": None}}
    return resp


def _mock_response_no_price():
    resp = MagicMock()
    resp.json.return_value = {
        "chart": {
            "result": [{"meta": {"regularMarketPrice": None}, "indicators": {"quote": [{}]}}]
        }
    }
    return resp


# ─── _fetch_chart ─────────────────────────────────────────────────────────────

class TestFetchChart:

    def test_tw_success_returns_result(self):
        with patch("yahoo_finance_api.requests.get", return_value=_mock_response_ok()) as mock_get:
            result = yf._fetch_chart("2330")
        assert result is not None
        assert result["meta"]["regularMarketPrice"] == 1000.0
        # 只應呼叫一次 (.TW 成功後不再試 .TWO)
        assert mock_get.call_count == 1
        assert ".TW" in mock_get.call_args[0][0]

    def test_tw_fails_fallback_to_two(self):
        """上市 .TW 失敗時，自動嘗試上櫃 .TWO"""
        call_count = [0]

        def side_effect(url, **kwargs):
            call_count[0] += 1
            if ".TW?" in url and ".TWO" not in url:
                return _mock_response_empty()  # .TW 失敗
            return _mock_response_ok()  # .TWO 成功

        with patch("yahoo_finance_api.requests.get", side_effect=side_effect):
            result = yf._fetch_chart("6488")

        assert result is not None
        assert call_count[0] == 2  # .TW + .TWO 各一次

    def test_both_fail_returns_none(self):
        with patch("yahoo_finance_api.requests.get", return_value=_mock_response_empty()):
            result = yf._fetch_chart("9999")
        assert result is None

    def test_exception_on_tw_fallback_to_two(self):
        """網路異常時也應嘗試 .TWO"""
        def side_effect(url, **kwargs):
            if ".TW?" in url and ".TWO" not in url:
                raise Exception("connection timeout")
            return _mock_response_ok()

        with patch("yahoo_finance_api.requests.get", side_effect=side_effect):
            result = yf._fetch_chart("6488")

        assert result is not None

    def test_no_regular_market_price_skips(self):
        """meta.regularMarketPrice 為 None，視同失敗"""
        with patch("yahoo_finance_api.requests.get", return_value=_mock_response_no_price()):
            result = yf._fetch_chart("2330")
        assert result is None


# ─── get_current_price ────────────────────────────────────────────────────────

class TestGetCurrentPrice:

    def test_returns_price(self):
        with patch("yahoo_finance_api._fetch_chart", return_value=_make_chart_result(price=1050.0)):
            price = yf.get_current_price("2330")
        assert price == 1050.0

    def test_returns_none_on_failure(self):
        with patch("yahoo_finance_api._fetch_chart", return_value=None):
            price = yf.get_current_price("9999")
        assert price is None


# ─── get_previous_close ───────────────────────────────────────────────────────

class TestGetPreviousClose:

    def test_from_meta(self):
        with patch("yahoo_finance_api._fetch_chart", return_value=_make_chart_result(prev_close=980.0)):
            prev = yf.get_previous_close("2330")
        assert prev == 980.0

    def test_from_indicators_when_meta_missing(self):
        result = _make_chart_result(closes=[900.0, 950.0])
        result["meta"].pop("previousClose", None)  # 移除 meta.previousClose

        with patch("yahoo_finance_api._fetch_chart", return_value=result):
            prev = yf.get_previous_close("2330")
        # 應從 indicators 的第二筆取（closes[-2]）
        assert prev == 900.0

    def test_returns_none_on_failure(self):
        with patch("yahoo_finance_api._fetch_chart", return_value=None):
            prev = yf.get_previous_close("9999")
        assert prev is None


# ─── get_5day_change ──────────────────────────────────────────────────────────

class TestGet5DayChange:

    def test_positive_change(self):
        # 首日 900, 末日 1000 → +11.1%
        result = _make_chart_result(closes=[900.0, 920.0, 950.0, 980.0, 1000.0])
        with patch("yahoo_finance_api._fetch_chart", return_value=result):
            change = yf.get_5day_change("2330")
        expected = (1000 - 900) / 900 * 100
        assert abs(change - expected) < 0.01

    def test_negative_change(self):
        result = _make_chart_result(closes=[1000.0, 980.0, 960.0, 940.0, 900.0])
        with patch("yahoo_finance_api._fetch_chart", return_value=result):
            change = yf.get_5day_change("2330")
        expected = (900 - 1000) / 1000 * 100
        assert abs(change - expected) < 0.01

    def test_single_data_point_returns_none(self):
        result = _make_chart_result(closes=[1000.0])
        with patch("yahoo_finance_api._fetch_chart", return_value=result):
            change = yf.get_5day_change("2330")
        assert change is None

    def test_returns_none_on_failure(self):
        with patch("yahoo_finance_api._fetch_chart", return_value=None):
            change = yf.get_5day_change("9999")
        assert change is None


# ─── get_history ──────────────────────────────────────────────────────────────

class TestGetHistory:

    def test_returns_structure(self):
        with patch("yahoo_finance_api._fetch_chart", return_value=_make_chart_result()):
            hist = yf.get_history("2330", period="5d")
        assert hist is not None
        assert "timestamps" in hist
        assert "closes" in hist
        assert "volumes" in hist
        assert "opens" in hist
        assert "highs" in hist
        assert "lows" in hist

    def test_returns_none_on_failure(self):
        with patch("yahoo_finance_api._fetch_chart", return_value=None):
            hist = yf.get_history("9999")
        assert hist is None
