#!/usr/bin/env python3
"""
美股龍頭股預警系統 (v1.0)
用於盤前分析時自動偵測美股龍頭股暴跌，並排除受影響的台股產業

功能：
- 讀取 fetch_us_asia_markets.py 產生的數據
- 偵測龍頭股暴跌（Micron, NVIDIA, Apple, AMD, Tesla）
- 自動建立「龍頭股→台股產業」對應表
- 產生預警等級（Level 0-3）+ 排除清單

使用方法：
python scripts/us_leader_alert.py
python scripts/us_leader_alert.py --date 2026-02-10
"""

import sys
import io
import json
import os
import datetime
from typing import Dict, List, Any, Tuple

# Windows 環境 stdout 編碼修正
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ============================================================
# 龍頭股→台股產業對應表（從外部 JSON 讀取）
# ============================================================

def _load_leader_mapping():
    """從 data/us_leader_mapping.json 讀取對應表"""
    mapping_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'us_leader_mapping.json')
    mapping_file = os.path.abspath(mapping_file)
    try:
        with open(mapping_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # 轉換格式：只保留有 tw_stocks 的龍頭（預警需要台股對應）
        result = {}
        for name, info in data.get('leaders', {}).items():
            if info.get('tw_stocks'):
                result[name] = {
                    'tw_industry': info['tw_industry'],
                    'tw_stocks': info['tw_stocks'],
                    'threshold_l3': info.get('threshold_l3', -10),
                    'threshold_l2': info.get('threshold_l2', -5),
                    'threshold_l1': info.get('threshold_l1', -2),
                }
        return result
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[WARN] 無法讀取 {mapping_file}: {e}", file=sys.stderr)
        return {}

US_LEADER_MAPPING = _load_leader_mapping()


# ============================================================
# 預警等級定義
# ============================================================

LEVEL_DEFINITIONS = {
    'level_3': {
        'name': '🔴 直接排除',
        'description': '龍頭股暴跌，相關產業高風險',
        'action': 'exclude',
        'score_adjustment': 0  # 直接排除，不進入評分
    },
    'level_2': {
        'name': '🟡 降級評分',
        'description': '龍頭股跌幅明顯，相關產業需謹慎',
        'action': 'downgrade',
        'score_adjustment': -15  # 五維度評分扣 15 分
    },
    'level_1': {
        'name': '⚪ 提示注意',
        'description': '龍頭股小跌，相關產業需注意',
        'action': 'warning',
        'score_adjustment': -5  # 五維度評分扣 5 分
    },
    'level_0': {
        'name': '✅ 正常/利多',
        'description': '龍頭股表現正常或上漲',
        'action': 'normal',
        'score_adjustment': 0  # 不調整（或在五維度評分中加分）
    }
}


# ============================================================
# 主邏輯
# ============================================================

class USLeaderAlertSystem:
    """美股龍頭股預警系統"""

    def __init__(self, date: str = None):
        """
        Args:
            date: 日期（YYYY-MM-DD），預設為今日
        """
        if date is None:
            self.date = datetime.datetime.now().strftime('%Y-%m-%d')
        else:
            self.date = date

        self.data_dir = os.path.join('data', self.date)
        self.alerts = []
        self.excluded_stocks = set()
        self.downgraded_stocks = {}
        self.warning_stocks = {}

    def load_us_market_data(self) -> Dict[str, float]:
        """讀取美股市場數據"""
        json_file = os.path.join(self.data_dir, 'us_asia_markets.json')

        if not os.path.exists(json_file):
            raise FileNotFoundError(
                f"❌ 找不到美股數據檔案：{json_file}\n"
                f"   請先執行：python scripts/fetch_us_asia_markets.py --output-dir data/{self.date}"
            )

        # 讀取檔案內容（可能包含混合格式：終端輸出 + JSON）
        with open(json_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 嘗試直接解析 JSON
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # 如果失敗，嘗試提取 JSON 部分（從第一個 { 到最後一個 }）
            json_start = content.find('{')
            json_end = content.rfind('}')
            if json_start != -1 and json_end != -1:
                json_content = content[json_start:json_end + 1]
                data = json.loads(json_content)
            else:
                raise ValueError(f"無法從檔案中提取 JSON：{json_file}")

        print(f"✅ 已讀取美股數據：{json_file}", file=sys.stderr)
        return data

    def determine_alert_level(self, change_pct: float, thresholds: Dict[str, float]) -> int:
        """
        判斷預警等級

        Args:
            change_pct: 漲跌幅（%）
            thresholds: 門檻值字典

        Returns:
            0-3 的等級
        """
        if change_pct < thresholds['threshold_l3']:
            return 3
        elif change_pct < thresholds['threshold_l2']:
            return 2
        elif change_pct < thresholds['threshold_l1']:
            return 1
        else:
            return 0

    def analyze_leader_stock(self, leader_name: str, change_pct: float) -> Dict[str, Any]:
        """
        分析單一龍頭股

        Args:
            leader_name: 龍頭股名稱（如 'Micron'）
            change_pct: 漲跌幅（%）

        Returns:
            預警資訊字典
        """
        if leader_name not in US_LEADER_MAPPING:
            return None

        mapping = US_LEADER_MAPPING[leader_name]
        level = self.determine_alert_level(change_pct, mapping)

        if level == 0:
            return None  # 正常情況不產生預警

        level_info = LEVEL_DEFINITIONS[f'level_{level}']

        alert = {
            'us_stock': leader_name,
            'change_pct': change_pct,
            'level': level,
            'level_name': level_info['name'],
            'tw_industry': mapping['tw_industry'],
            'affected_stocks': mapping['tw_stocks'],
            'action': level_info['action'],
            'score_adjustment': level_info['score_adjustment'],
            'reason': f"{leader_name} 跌幅 {change_pct:+.2f}%，{mapping['tw_industry']}產業受壓"
        }

        # 記錄受影響股票
        if level == 3:
            self.excluded_stocks.update(mapping['tw_stocks'].keys())
        elif level == 2:
            for code in mapping['tw_stocks'].keys():
                self.downgraded_stocks[code] = {
                    'reason': f"{leader_name} 跌幅 {change_pct:+.2f}%",
                    'adjustment': level_info['score_adjustment']
                }
        elif level == 1:
            for code in mapping['tw_stocks'].keys():
                self.warning_stocks[code] = {
                    'reason': f"{leader_name} 跌幅 {change_pct:+.2f}%",
                    'adjustment': level_info['score_adjustment']
                }

        return alert

    def analyze_all_leaders(self, us_data: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        分析所有龍頭股

        Args:
            us_data: 美股數據字典（key=股票名稱, value=漲跌幅）

        Returns:
            預警列表
        """
        alerts = []

        for leader_name in US_LEADER_MAPPING.keys():
            if leader_name in us_data:
                change_pct = us_data[leader_name]
                alert = self.analyze_leader_stock(leader_name, change_pct)
                if alert:
                    alerts.append(alert)

        return alerts

    def generate_summary(self) -> Dict[str, Any]:
        """產生摘要統計"""
        level_counts = {0: 0, 1: 0, 2: 0, 3: 0}
        for alert in self.alerts:
            level_counts[alert['level']] += 1

        return {
            'date': self.date,
            'total_alerts': len(self.alerts),
            'level_3_count': level_counts[3],
            'level_2_count': level_counts[2],
            'level_1_count': level_counts[1],
            'excluded_stocks': list(self.excluded_stocks),
            'downgraded_stocks': self.downgraded_stocks,
            'warning_stocks': self.warning_stocks
        }

    def format_markdown(self) -> str:
        """格式化為 Markdown 輸出（人類閱讀）"""
        lines = []
        lines.append(f"# 🚨 美股龍頭預警報告")
        lines.append(f"**日期**：{self.date}")
        lines.append("")

        if not self.alerts:
            lines.append("✅ **無預警**：所有龍頭股表現正常")
            return "\n".join(lines)

        # 按等級分組
        level_3_alerts = [a for a in self.alerts if a['level'] == 3]
        level_2_alerts = [a for a in self.alerts if a['level'] == 2]
        level_1_alerts = [a for a in self.alerts if a['level'] == 1]

        if level_3_alerts:
            lines.append("## 🔴 Level 3：直接排除（暴跌警示）")
            lines.append("")
            for alert in level_3_alerts:
                lines.append(f"### {alert['us_stock']} ({alert['change_pct']:+.2f}%)")
                lines.append(f"- **受影響產業**：{alert['tw_industry']}")
                lines.append(f"- **受影響股票**：{len(alert['affected_stocks'])} 檔")
                for code, name in alert['affected_stocks'].items():
                    lines.append(f"  - {name}({code})")
                lines.append(f"- **動作**：🚫 **直接排除，不進入評分**")
                lines.append(f"- **原因**：{alert['reason']}")
                lines.append("")

        if level_2_alerts:
            lines.append("## 🟡 Level 2：降級評分（明顯下跌）")
            lines.append("")
            for alert in level_2_alerts:
                lines.append(f"### {alert['us_stock']} ({alert['change_pct']:+.2f}%)")
                lines.append(f"- **受影響產業**：{alert['tw_industry']}")
                lines.append(f"- **受影響股票**：{len(alert['affected_stocks'])} 檔")
                for code, name in alert['affected_stocks'].items():
                    lines.append(f"  - {name}({code})")
                lines.append(f"- **動作**：⚠️ 五維度評分 **-15分**")
                lines.append(f"- **原因**：{alert['reason']}")
                lines.append("")

        if level_1_alerts:
            lines.append("## ⚪ Level 1：提示注意（小幅下跌）")
            lines.append("")
            for alert in level_1_alerts:
                lines.append(f"### {alert['us_stock']} ({alert['change_pct']:+.2f}%)")
                lines.append(f"- **受影響產業**：{alert['tw_industry']}")
                lines.append(f"- **受影響股票**：{len(alert['affected_stocks'])} 檔")
                for code, name in alert['affected_stocks'].items():
                    lines.append(f"  - {name}({code})")
                lines.append(f"- **動作**：ℹ️ 五維度評分 **-5分**，持續觀察")
                lines.append(f"- **原因**：{alert['reason']}")
                lines.append("")

        # 總結
        lines.append("---")
        lines.append("## 📊 總結")
        lines.append("")
        lines.append(f"- **總預警數**：{len(self.alerts)} 個")
        lines.append(f"- **Level 3（直接排除）**：{len(level_3_alerts)} 個")
        lines.append(f"- **Level 2（降級評分）**：{len(level_2_alerts)} 個")
        lines.append(f"- **Level 1（提示注意）**：{len(level_1_alerts)} 個")
        lines.append("")
        lines.append(f"- **被排除股票**：{len(self.excluded_stocks)} 檔")
        if self.excluded_stocks:
            excluded_list = []
            for code in self.excluded_stocks:
                for alert in level_3_alerts:
                    if code in alert['affected_stocks']:
                        excluded_list.append(f"{alert['affected_stocks'][code]}({code})")
                        break
            lines.append(f"  - {', '.join(excluded_list)}")

        return "\n".join(lines)

    def run(self) -> Tuple[Dict[str, Any], str]:
        """
        執行預警系統

        Returns:
            (JSON 數據, Markdown 文字)
        """
        print(f"🚨 美股龍頭預警系統 v1.0", file=sys.stderr)
        print(f"📅 分析日期：{self.date}", file=sys.stderr)
        print("=" * 60, file=sys.stderr)

        # 讀取美股數據
        us_data = self.load_us_market_data()

        # 分析所有龍頭股
        print("🔍 分析龍頭股...", file=sys.stderr)
        self.alerts = self.analyze_all_leaders(us_data)

        # 產生摘要
        summary = self.generate_summary()

        # 格式化輸出
        markdown = self.format_markdown()

        # 整合結果
        result = {
            'alerts': self.alerts,
            'summary': summary
        }

        print("=" * 60, file=sys.stderr)
        print(f"✅ 分析完成", file=sys.stderr)
        print(f"   總預警數：{summary['total_alerts']}", file=sys.stderr)
        print(f"   Level 3：{summary['level_3_count']} 個", file=sys.stderr)
        print(f"   被排除股票：{len(self.excluded_stocks)} 檔", file=sys.stderr)

        return result, markdown


# ============================================================
# CLI 介面
# ============================================================

def main():
    """主執行函數"""
    import argparse

    parser = argparse.ArgumentParser(description='美股龍頭預警系統')
    parser.add_argument('--date', type=str, default=None,
                        help='分析日期（YYYY-MM-DD），預設為今日')
    parser.add_argument('--format', choices=['json', 'markdown', 'both'], default='both',
                        help='輸出格式：json, markdown, both（預設）')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='輸出目錄（如果指定，會寫入文件而非stdout）')
    args = parser.parse_args()

    # 執行預警系統
    system = USLeaderAlertSystem(date=args.date)

    try:
        result_json, result_markdown = system.run()
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    # 輸出結果
    if args.output_dir:
        # 輸出到文件
        os.makedirs(args.output_dir, exist_ok=True)

        if args.format in ['json', 'both']:
            json_file = os.path.join(args.output_dir, 'us_leader_alerts.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(result_json, f, ensure_ascii=False, indent=2)
            print(f"✅ JSON 已保存：{json_file}", file=sys.stderr)

        if args.format in ['markdown', 'both']:
            md_file = os.path.join(args.output_dir, 'us_leader_alerts.md')
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(result_markdown)
            print(f"✅ Markdown 已保存：{md_file}", file=sys.stderr)
    else:
        # 輸出到 stdout
        if args.format == 'json':
            print(json.dumps(result_json, ensure_ascii=False, indent=2))
        elif args.format == 'markdown':
            print(result_markdown)
        else:  # both
            # JSON 到 stdout
            print(json.dumps(result_json, ensure_ascii=False, indent=2))
            # Markdown 到 stderr
            print("\n" + "=" * 60, file=sys.stderr)
            print("📋 Markdown 格式（人類閱讀）：", file=sys.stderr)
            print("=" * 60, file=sys.stderr)
            print(result_markdown, file=sys.stderr)


if __name__ == "__main__":
    main()
