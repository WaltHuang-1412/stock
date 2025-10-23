"""
每日摘要生成器

从盘后分析报告中提取关键信息，生成简洁的每日摘要
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


class DailySummaryGenerator:
    """每日摘要生成器"""

    def __init__(self):
        self.date = None
        self.predictions = []
        self.lessons = []
        self.tomorrow_strategy = {
            'recommend': [],
            'observe': [],
            'avoid': []
        }
        self.key_observations = []
        self.holdings_advice = []

    def parse_after_market_report(self, report_path: str) -> Dict:
        """
        解析盘后分析报告

        Args:
            report_path: 盘后分析报告路径

        Returns:
            解析后的结构化数据
        """
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取日期
            self.date = self._extract_date(content)

            # 提取预测验证结果
            self.predictions = self._extract_predictions(content)

            # 提取核心教训
            self.lessons = self._extract_lessons(content)

            # 提取明日策略
            self.tomorrow_strategy = self._extract_tomorrow_strategy(content)

            # 提取明日观察重点
            self.key_observations = self._extract_key_observations(content)

            # 提取持股建议
            self.holdings_advice = self._extract_holdings_advice(content)

            return self._compile_data()

        except Exception as e:
            print(f"解析盘后报告失败: {e}")
            return {}

    def _extract_date(self, content: str) -> str:
        """提取日期"""
        match = re.search(r'# (\d{4}-\d{2}-\d{2})', content)
        if match:
            return match.group(1)
        return datetime.now().strftime('%Y-%m-%d')

    def _extract_predictions(self, content: str) -> List[Dict]:
        """提取预测验证结果"""
        predictions = []

        # 提取统计结果
        success_match = re.search(r'- ✅ \*\*成功\*\*: (\d+)檔 \((\d+\.?\d*)%\)', content)
        fail_match = re.search(r'- ❌ \*\*失敗\*\*: (\d+)檔 \((\d+\.?\d*)%\)', content)

        if success_match and fail_match:
            predictions.append({
                'success_count': int(success_match.group(1)),
                'success_rate': float(success_match.group(2)),
                'fail_count': int(fail_match.group(1)),
                'fail_rate': float(fail_match.group(2))
            })

        # 提取成功案例
        success_section = re.search(r'#### 成功案例(.*?)(?:####|---)', content, re.DOTALL)
        if success_section:
            success_stocks = re.findall(r'\*\*\d+\. (.*?) \((\d+)\)\*\*: ([+-]\d+\.\d+%)', success_section.group(1))
            for name, symbol, change in success_stocks:
                predictions.append({
                    'type': 'success',
                    'name': name,
                    'symbol': symbol,
                    'change': change
                })

        # 提取失败案例
        fail_section = re.search(r'#### 重大失敗案例(.*?)(?:####|---)', content, re.DOTALL)
        if fail_section:
            fail_stocks = re.findall(r'\*\*\d+\. (.*?) \((\d+)\)\*\*: ([+-]\d+\.\d+%)', fail_section.group(1))
            for name, symbol, change in fail_stocks:
                predictions.append({
                    'type': 'fail',
                    'name': name,
                    'symbol': symbol,
                    'change': change
                })

        return predictions

    def _extract_lessons(self, content: str) -> List[str]:
        """提取核心教训"""
        lessons = []

        # 查找"今日三大教训"或"关键教训"部分
        lesson_section = re.search(r'### \d+\.\d+ 今日三大教訓(.*?)(?:###|---)', content, re.DOTALL)
        if not lesson_section:
            lesson_section = re.search(r'## 五、關鍵教訓(.*?)(?:##|---)', content, re.DOTALL)

        if lesson_section:
            # 提取带编号的教训
            lesson_items = re.findall(r'\*\*\d+\. (.*?)\*\*', lesson_section.group(1))
            lessons.extend(lesson_items[:5])  # 最多5条

        return lessons

    def _extract_tomorrow_strategy(self, content: str) -> Dict:
        """提取明日策略"""
        strategy = {
            'recommend': [],
            'observe': [],
            'avoid': []
        }

        # 提取强力推荐
        recommend_section = re.search(r'#### ⭐ 強力推薦(.*?)(?:####|###)', content, re.DOTALL)
        if recommend_section:
            stocks = re.findall(r'\*\*\d+\. (.*?) \((\d+)\)\*\*.*?佈局價位\*\*: (.*?)\n.*?目標價\*\*: (.*?)\n',
                              recommend_section.group(1), re.DOTALL)
            for name, symbol, entry, target in stocks:
                strategy['recommend'].append({
                    'name': name,
                    'symbol': symbol,
                    'entry': entry.strip(),
                    'target': target.strip()
                })

        # 提取观察佈局
        observe_section = re.search(r'#### ⚠️ 觀察佈局.*?\n(.*?)(?:###|##)', content, re.DOTALL)
        if observe_section:
            stocks = re.findall(r'\*\*\d+\. (.*?) \((\d+)\)\*\*.*?佈局價位\*\*: (.*?)\n',
                              observe_section.group(1), re.DOTALL)
            for name, symbol, entry in stocks:
                strategy['observe'].append({
                    'name': name,
                    'symbol': symbol,
                    'entry': entry.strip()
                })

        # 提取避开清单
        avoid_section = re.search(r'#### ❌ 絕對避開(.*?)(?:###|##)', content, re.DOTALL)
        if avoid_section:
            avoid_items = re.findall(r'\*\*\d+\. (.*?)\*\*', avoid_section.group(1))
            strategy['avoid'] = avoid_items

        return strategy

    def _extract_key_observations(self, content: str) -> List[str]:
        """提取明日观察重点"""
        observations = []

        # 查找"明日重点观察"部分
        obs_section = re.search(r'\*\*📌 明日重點觀察\*\*(.*?)(?:##|---|\Z)', content, re.DOTALL)
        if obs_section:
            obs_items = re.findall(r'\d+\. (.*?)(?:\n|$)', obs_section.group(1))
            observations.extend([item.strip() for item in obs_items])

        return observations

    def _extract_holdings_advice(self, content: str) -> List[Dict]:
        """提取持股建议"""
        holdings = []

        # 查找持股操作建议表格
        holdings_section = re.search(r'\| 代號 \| 名稱 \| 成本 \| .*? \| 損益% \| 明日策略 \|(.*?)(?:\n\n|---)',
                                    content, re.DOTALL)
        if holdings_section:
            rows = re.findall(r'\| (\d+) \| (.*?) \| (.*?) \| (.*?) \| (.*?) \| (.*?) \|',
                            holdings_section.group(1))
            for symbol, name, cost, price, profit, strategy in rows:
                holdings.append({
                    'symbol': symbol.strip(),
                    'name': name.strip(),
                    'cost': cost.strip(),
                    'price': price.strip(),
                    'profit': profit.strip(),
                    'strategy': strategy.strip()
                })

        return holdings

    def _compile_data(self) -> Dict:
        """编译所有提取的数据"""
        return {
            'date': self.date,
            'predictions': self.predictions,
            'lessons': self.lessons,
            'tomorrow_strategy': self.tomorrow_strategy,
            'key_observations': self.key_observations,
            'holdings_advice': self.holdings_advice
        }

    def generate_summary(self, data: Dict) -> str:
        """
        生成每日摘要

        Args:
            data: 解析后的数据

        Returns:
            格式化的摘要文本
        """
        date = data.get('date', 'N/A')
        predictions = data.get('predictions', [])
        lessons = data.get('lessons', [])
        strategy = data.get('tomorrow_strategy', {})
        observations = data.get('key_observations', [])
        holdings = data.get('holdings_advice', [])

        # 生成摘要
        summary = f"""# {date} 每日精華結論

**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**數據來源**: 盤後完整分析報告

---

## 📊 預測成績單

"""

        # 预测统计
        if predictions:
            stats = predictions[0] if predictions[0].get('success_rate') else None
            if stats:
                summary += f"""**準確率**: {stats['success_rate']:.1f}% ({stats['success_count']}/{stats['success_count'] + stats['fail_count']}檔)

"""

            # 成功案例
            success_cases = [p for p in predictions if p.get('type') == 'success']
            if success_cases:
                summary += "### ✅ 成功案例\n\n"
                for case in success_cases[:3]:  # 最多3个
                    summary += f"- **{case['name']} ({case['symbol']})**: {case['change']}\n"
                summary += "\n"

            # 失败案例
            fail_cases = [p for p in predictions if p.get('type') == 'fail']
            if fail_cases:
                summary += "### ❌ 失敗案例\n\n"
                for case in fail_cases[:3]:  # 最多3个
                    summary += f"- **{case['name']} ({case['symbol']})**: {case['change']}\n"
                summary += "\n"

        # 核心教训
        if lessons:
            summary += "## 🎯 核心教訓\n\n"
            for i, lesson in enumerate(lessons, 1):
                summary += f"{i}. {lesson}\n"
            summary += "\n"

        # 明日策略
        summary += "---\n\n## 📈 明日佈局策略\n\n"

        # 强力推荐
        if strategy.get('recommend'):
            summary += "### ⭐ 強力推薦\n\n"
            for stock in strategy['recommend']:
                summary += f"**{stock['name']} ({stock['symbol']})**\n"
                summary += f"- 佈局價位: {stock['entry']}\n"
                summary += f"- 目標價: {stock['target']}\n\n"

        # 观察佈局
        if strategy.get('observe'):
            summary += "### ⚠️ 觀察佈局（等訊號）\n\n"
            for stock in strategy['observe']:
                summary += f"- **{stock['name']} ({stock['symbol']})**: {stock['entry']}\n"
            summary += "\n"

        # 避开清单
        if strategy.get('avoid'):
            summary += "### ❌ 避開清單\n\n"
            for item in strategy['avoid'][:5]:  # 最多5个
                summary += f"- {item}\n"
            summary += "\n"

        # 明日观察重点
        if observations:
            summary += "---\n\n## 🔍 明日關鍵觀察\n\n"
            for obs in observations:
                summary += f"- {obs}\n"
            summary += "\n"

        # 持股建议
        if holdings:
            summary += "---\n\n## 💼 持股操作建議\n\n"
            summary += "| 代號 | 名稱 | 損益% | 明日策略 |\n"
            summary += "|------|------|-------|----------|\n"
            for h in holdings:
                summary += f"| {h['symbol']} | {h['name']} | {h['profit']} | {h['strategy']} |\n"
            summary += "\n"

        # 结尾
        summary += """---

## ⚠️ 風險提示

本摘要僅供快速決策參考，詳細分析請參閱完整盤後報告。

**投資有風險，請謹慎決策，並嚴守停損紀律。**

---

**完整報告**: `after_market_analysis.md`
**下次更新**: 明日 09:00（盤前分析）
"""

        return summary

    def save_summary(self, summary: str, output_path: str):
        """
        保存摘要到文件

        Args:
            summary: 摘要内容
            output_path: 输出路径
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(summary)

            print(f"✅ 每日摘要已生成: {output_path}")

        except Exception as e:
            print(f"❌ 保存摘要失败: {e}")

    def generate_from_file(self, report_path: str, output_path: str):
        """
        从盘后报告生成摘要（便捷方法）

        Args:
            report_path: 盘后分析报告路径
            output_path: 输出路径
        """
        print(f"正在解析盘后报告: {report_path}")
        data = self.parse_after_market_report(report_path)

        if not data:
            print("❌ 解析失败，无法生成摘要")
            return

        print("正在生成每日摘要...")
        summary = self.generate_summary(data)

        print(f"正在保存到: {output_path}")
        self.save_summary(summary, output_path)


def main():
    """命令行使用示例"""
    import sys

    if len(sys.argv) < 2:
        print("用法: python daily_summary_generator.py <盘后报告路径> [输出路径]")
        print("\n示例:")
        print("  python daily_summary_generator.py data/2025-10-21/after_market_analysis.md")
        print("  python daily_summary_generator.py data/2025-10-21/after_market_analysis.md data/2025-10-21/daily_summary.md")
        return

    report_path = sys.argv[1]

    # 自动生成输出路径
    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        report_file = Path(report_path)
        output_path = report_file.parent / 'daily_summary.md'

    # 生成摘要
    generator = DailySummaryGenerator()
    generator.generate_from_file(report_path, output_path)


if __name__ == '__main__':
    main()
