from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QComboBox, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QSplitter, QScrollArea, QWidget, QSizePolicy, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

import skin_engine as S
from stats_charts import PieChartWidget, BarChartWidget, StatsChartCard, refresh_chart_skin

import os
from datetime import datetime


def _c(key, fallback):
    try:
        value = S.current()["c"].get(key)
        return value if value else fallback
    except Exception:
        return fallback


def _f(key, fallback):
    try:
        value = S.current()["f"].get(key)
        return value if value else fallback
    except Exception:
        return fallback


def _fam():
    return _f("family", "Microsoft YaHei")


def _font(size, bold=False):
    font = QFont(_fam(), max(7, int(size)))
    font.setBold(bool(bold))
    return font


class MetricCard(QFrame):
    def __init__(self, key, title, accent, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(76)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(2)

        head = QHBoxLayout()
        head.setSpacing(6)
        self.dot = QLabel()
        self.dot.setFixedSize(8, 8)
        head.addWidget(self.dot)
        self.title = QLabel(title)
        head.addWidget(self.title)
        head.addStretch()
        layout.addLayout(head)

        self.value = QLabel("0")
        layout.addWidget(self.value)

        self._accent = accent
        self.refresh_skin()

    def refresh_skin(self):
        base = int(_f("size", 13))
        self.title.setStyleSheet(
            "font-family: \"%s\"; font-size: %dpx; color: %s; background: transparent;"
            % (_fam(), max(9, base - 3), _c("text3", "#666666"))
        )
        self.dot.setStyleSheet("background: %s; border-radius: 4px;" % _c(self._accent, "#0067c0"))
        self.value.setStyleSheet(
            "font-family: \"%s\"; font-size: %dpx; font-weight: 800; color: %s; background: transparent;"
            % (_fam(), max(16, int(base * 1.7)), _c("text", "#1b1b1b"))
        )


class StatsDialog(QDialog):
    def __init__(self, data_mgr, parent=None):
        super().__init__(parent)
        self.data_mgr = data_mgr
        self.setWindowTitle("数据统计")
        self.setObjectName("settingsroot")
        self.setMinimumSize(880, 640)
        self.resize(940, 720)
        self._build()
        self._load_data()

    def _build(self):
        base = int(_f("size", 13))
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 14)
        outer.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(10)
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.title = QLabel("数据统计")
        title_box.addWidget(self.title)
        self.subtitle = QLabel("课堂背诵状态、抽取次数与积分的汇总视图")
        title_box.addWidget(self.subtitle)
        header.addLayout(title_box)
        header.addStretch()
        self.scope_chip = QLabel("全部轮次")
        header.addWidget(self.scope_chip)
        outer.addLayout(header)

        bar = QFrame()
        bar.setObjectName("card")
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(14, 10, 14, 10)
        bar_layout.setSpacing(8)
        self.round_label = QLabel("轮次")
        bar_layout.addWidget(self.round_label)
        self.round_selector = QComboBox()
        self.round_selector.setMinimumWidth(260)
        self.round_selector.currentIndexChanged.connect(self._on_round_selected)
        bar_layout.addWidget(self.round_selector)
        self.round_info_label = QLabel("共 0 轮")
        bar_layout.addWidget(self.round_info_label)
        bar_layout.addStretch()
        self.delete_btn = QPushButton("删除此轮")
        self.delete_btn.setObjectName("danger")
        self.delete_btn.setFixedHeight(34)
        self.delete_btn.clicked.connect(self._delete_round)
        bar_layout.addWidget(self.delete_btn)
        outer.addWidget(bar)

        metrics = QHBoxLayout()
        metrics.setSpacing(10)
        self.metric_cards = {}
        for key, text, accent in [
            ("total", "总抽取", "primary"),
            ("mastered", "已背过", "success"),
            ("familiar", "未背熟", "warning"),
            ("unlearned", "未背过", "danger"),
            ("avg_score", "平均积分", "accent"),
        ]:
            card = MetricCard(key, text, accent)
            metrics.addWidget(card)
            self.metric_cards[key] = card
        outer.addLayout(metrics)

        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)

        charts_tabs = QTabWidget()
        page_overview = QWidget()
        overview_layout = QHBoxLayout(page_overview)
        overview_layout.setContentsMargins(6, 8, 6, 6)
        overview_layout.setSpacing(10)
        self.pie_chart = PieChartWidget("")
        self.pie_chart.setMinimumHeight(230)
        overview_layout.addWidget(StatsChartCard("背诵状态分布", self.pie_chart), 1)
        self.bar_chart = BarChartWidget("", max_items=10)
        self.bar_chart.setMinimumHeight(230)
        overview_layout.addWidget(StatsChartCard("抽取次数 Top 10", self.bar_chart), 1)
        charts_tabs.addTab(page_overview, "总览")

        page_score = QWidget()
        score_layout = QVBoxLayout(page_score)
        score_layout.setContentsMargins(6, 8, 6, 6)
        self.score_chart = BarChartWidget("", max_items=10)
        self.score_chart.setMinimumHeight(220)
        self.score_chart.set_bar_color(_c("accent", "#8764b8"))
        score_layout.addWidget(StatsChartCard("积分排名 Top 10", self.score_chart))
        charts_tabs.addTab(page_score, "积分")

        page_text = QWidget()
        text_layout = QVBoxLayout(page_text)
        text_layout.setContentsMargins(6, 8, 6, 6)
        self.text_bar_chart = BarChartWidget("", max_items=8)
        self.text_bar_chart.setMinimumHeight(220)
        self.text_bar_chart.set_bar_color(_c("warning", "#ca5010"))
        text_layout.addWidget(StatsChartCard("课文抽取次数", self.text_bar_chart))
        charts_tabs.addTab(page_text, "课文")
        splitter.addWidget(charts_tabs)

        tables_tabs = QTabWidget()
        self.records_table = self._make_table(["时间", "学生", "课文", "段落", "状态", "轮次"])
        tables_tabs.addTab(self.records_table, "抽取记录")
        self.table = self._make_table(["学生", "抽取次数", "已背过", "未背熟", "未背过", "积分"])
        tables_tabs.addTab(self.table, "学生明细")
        splitter.addWidget(tables_tabs)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        outer.addWidget(splitter, 1)

        footer = QHBoxLayout()
        footer.setSpacing(8)
        self.hint = QLabel("")
        footer.addWidget(self.hint)
        footer.addStretch()
        self.export_btn = QPushButton("导出数据")
        self.export_btn.setFixedHeight(38)
        self.export_btn.clicked.connect(self._export)
        footer.addWidget(self.export_btn)
        self.close_btn = QPushButton("关闭")
        self.close_btn.setObjectName("primary")
        self.close_btn.setFixedHeight(38)
        self.close_btn.setMinimumWidth(96)
        self.close_btn.clicked.connect(self.close)
        footer.addWidget(self.close_btn)
        outer.addLayout(footer)

        self._apply_local_skin(base)

    def _make_table(self, headers):
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        header = table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        stretch_index = headers.index("课文") if "课文" in headers else len(headers) - 1
        header.setSectionResizeMode(stretch_index, QHeaderView.Stretch)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setAlternatingRowColors(False)
        table.verticalHeader().setVisible(False)
        table.setStyleSheet(
            "QTableWidget { background: %s; color: %s; border: 1px solid %s; border-radius: 8px;"
            " gridline-color: %s; selection-background-color: %s; selection-color: %s; }"
            " QTableWidget::item { padding: 6px; }"
            " QHeaderView::section { background: %s; color: %s; border: none; padding: 7px; font-weight: 700; }"
            % (
                _c("card", "#ffffff"), _c("text", "#1b1b1b"), _c("border", "#e0e0e0"),
                _c("border", "#e0e0e0"), _c("sel", "#e5f3ff"), _c("text", "#1b1b1b"),
                _c("card2", "#f2f4f7"), _c("text2", "#4b4b4b"),
            )
        )
        return table

    def _apply_local_skin(self, base):
        self.title.setStyleSheet(
            "font-family: \"%s\"; font-size: %dpx; font-weight: 800; color: %s; background: transparent;"
            % (_fam(), max(18, int(base * 1.4)), _c("text", "#1b1b1b"))
        )
        self.subtitle.setStyleSheet(
            "font-family: \"%s\"; font-size: %dpx; color: %s; background: transparent;"
            % (_fam(), max(9, base - 3), _c("text3", "#7a7a7a"))
        )
        self.scope_chip.setStyleSheet(
            "font-family: \"%s\"; font-size: %dpx; font-weight: 700; color: %s;"
            " background: %s; border-radius: 10px; padding: 3px 12px;"
            % (_fam(), max(9, base - 3), _c("primary", "#0067c0"), _c("sel", "#e5f3ff"))
        )
        self.round_label.setStyleSheet(
            "font-family: \"%s\"; font-size: %dpx; color: %s; background: transparent;"
            % (_fam(), max(9, base - 2), _c("text2", "#4b4b4b"))
        )
        self.round_info_label.setStyleSheet(
            "font-family: \"%s\"; font-size: %dpx; color: %s; background: transparent;"
            % (_fam(), max(9, base - 3), _c("text3", "#7a7a7a"))
        )
        self.hint.setStyleSheet(
            "font-family: \"%s\"; font-size: %dpx; color: %s; background: transparent;"
            % (_fam(), max(9, base - 3), _c("text3", "#7a7a7a"))
        )
        self.round_selector.setStyleSheet(
            "QComboBox { padding: 5px 10px; border: 1px solid %s; border-radius: 7px;"
            " font-family: \"%s\"; font-size: %dpx; color: %s; background: %s; min-height: 24px; }"
            " QComboBox::drop-down { border: none; width: 20px; }"
            % (_c("border", "#dddddd"), _fam(), max(9, base - 2), _c("text", "#1b1b1b"), _c("input", "#ffffff"))
        )
        for card in self.metric_cards.values():
            card.refresh_skin()
        self.setStyleSheet("QDialog { background: %s; }" % _c("bg", "#f3f6fb"))

    def refresh_skin(self):
        self._apply_local_skin(int(_f("size", 13)))
        refresh_chart_skin(self)
        for chart in (self.pie_chart, self.bar_chart, self.score_chart, self.text_bar_chart):
            chart.update()

    def _load_data(self):
        self._load_rounds_to_selector()
        self._render_view(-1)

    def _set_scope(self, text, accent):
        self.scope_chip.setText(text)
        self.scope_chip.setStyleSheet(
            "font-family: \"%s\"; font-size: %dpx; font-weight: 700; color: %s;"
            " background: %s; border-radius: 10px; padding: 3px 12px;"
            % (_fam(), max(9, int(_f("size", 13)) - 3), _c(accent, "#0067c0"), _c("sel", "#e5f3ff"))
        )

    def _render_view(self, round_id):
        if round_id and round_id != -1:
            self._render_single_round(round_id)
        else:
            self._render_all_rounds()

    def _render_all_rounds(self):
        self._set_scope("全部轮次", "primary")
        stats = self.data_mgr.get_all_stats()
        self.table.setRowCount(len(stats))
        total_draw = total_mastered = total_familiar = total_unlearned = 0
        total_score = 0
        for row, (name, data) in enumerate(sorted(stats.items())):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(str(data["draw_count"])))
            self.table.setItem(row, 2, QTableWidgetItem(str(data["mastered"])))
            self.table.setItem(row, 3, QTableWidgetItem(str(data["familiar"])))
            self.table.setItem(row, 4, QTableWidgetItem(str(data["unlearned"])))
            self.table.setItem(row, 5, QTableWidgetItem(str(data["score"])))
            total_draw += data["draw_count"]
            total_mastered += data["mastered"]
            total_familiar += data["familiar"]
            total_unlearned += data["unlearned"]
            total_score += data["score"]
        self._set_metrics(total_draw, total_mastered, total_familiar, total_unlearned)
        self.metric_cards["avg_score"].value.setText(str(total_score // len(stats) if stats else 0))
        self.pie_chart.set_data([("已背过", total_mastered), ("未背熟", total_familiar), ("未背过", total_unlearned)])
        draw_data = sorted([(n, d["draw_count"]) for n, d in stats.items()], key=lambda x: x[1], reverse=True)
        self.bar_chart.set_data(draw_data)
        score_data = sorted([(n, d["score"]) for n, d in stats.items()], key=lambda x: x[1], reverse=True)
        self.score_chart.set_data(score_data)
        text_stats = self.data_mgr.get_text_stats()
        self.text_bar_chart.set_data(sorted([(t, d["total"]) for t, d in text_stats.items()], key=lambda x: x[1], reverse=True))
        self._fill_records_table(self.data_mgr.get_draw_records()[:200], -1)
        self.hint.setText("当前显示全部轮次累计数据")

    def _render_single_round(self, round_id):
        detail = self.data_mgr.get_round_detail(round_id)
        if not detail:
            return
        self._set_scope("第 %d 轮" % round_id, "warning")
        records = detail.get("records", [])
        total = len(records)
        mastered = sum(1 for r in records if r.get("status") == "已背过")
        familiar = sum(1 for r in records if r.get("status") == "未背熟")
        unlearned = sum(1 for r in records if r.get("status") == "未背过")
        self._set_metrics(total, mastered, familiar, unlearned)
        self.metric_cards["avg_score"].value.setText("-")
        self.pie_chart.set_data([("已背过", mastered), ("未背熟", familiar), ("未背过", unlearned)])
        per_student = {}
        per_text = {}
        for r in records:
            s = r.get("student", "")
            per_student[s] = per_student.get(s, 0) + 1
            t = r.get("text", "") or "未指定"
            per_text[t] = per_text.get(t, 0) + 1
        self.bar_chart.set_data(sorted(per_student.items(), key=lambda x: x[1], reverse=True))
        self.text_bar_chart.set_data(sorted(per_text.items(), key=lambda x: x[1], reverse=True))
        self.score_chart.set_data([])
        self.table.setRowCount(0)
        self._fill_records_table(list(reversed(records)), round_id)
        self.hint.setText("当前显示第 %d 轮的记录" % round_id)

    def _set_metrics(self, total, mastered, familiar, unlearned):
        self.metric_cards["total"].value.setText(str(total))
        self.metric_cards["mastered"].value.setText(str(mastered))
        self.metric_cards["familiar"].value.setText(str(familiar))
        self.metric_cards["unlearned"].value.setText(str(unlearned))

    def _fill_records_table(self, records, round_id):
        self.records_table.setRowCount(len(records))
        for row, rec in enumerate(records):
            rid = round_id if round_id and round_id != -1 else rec.get("round_id", 0)
            self.records_table.setItem(row, 0, QTableWidgetItem(rec.get("time", "")))
            self.records_table.setItem(row, 1, QTableWidgetItem(rec.get("student", "")))
            self.records_table.setItem(row, 2, QTableWidgetItem(rec.get("text", "")))
            self.records_table.setItem(row, 3, QTableWidgetItem(rec.get("paragraph", "")))
            self.records_table.setItem(row, 4, QTableWidgetItem(rec.get("status", "")))
            self.records_table.setItem(row, 5, QTableWidgetItem("第%d轮" % rid))

    def _export(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        path, _ = QFileDialog.getSaveFileName(
            self, "导出统计数据", os.path.join(desktop, "点名统计_%s.txt" % timestamp), "Text Files (*.txt)"
        )
        if not path:
            return
        try:
            stats = self.data_mgr.get_all_stats()
            with open(path, "w", encoding="utf-8") as f:
                f.write("课堂点名系统 - 统计数据\n")
                f.write("导出时间: %s\n" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                f.write("=" * 60 + "\n\n")
                f.write("%-12s%-10s%-10s%-10s%-10s%-10s\n" % ("学生", "抽取次数", "已背过", "未背熟", "未背过", "积分"))
                f.write("-" * 60 + "\n")
                for name, data in sorted(stats.items()):
                    f.write("%-12s%-10s%-10s%-10s%-10s%-10s\n" % (
                        name, data["draw_count"], data["mastered"], data["familiar"], data["unlearned"], data["score"]
                    ))
            QMessageBox.information(self, "导出成功", "统计数据已导出到：\n%s" % path)
        except Exception as e:
            QMessageBox.warning(self, "导出失败", "导出失败：%s" % str(e))

    def _load_rounds_to_selector(self):
        self.round_selector.blockSignals(True)
        self.round_selector.clear()
        rounds = self.data_mgr.get_all_rounds()
        self.round_selector.addItem("全部轮次", -1)
        for r in reversed(rounds):
            start_time = r.get("start_time", "")[:16] if r.get("start_time") else "未知"
            label = "第 %d 轮 · %s · %d人" % (r["round_id"], start_time, r["total"])
            self.round_selector.addItem(label, r["round_id"])
        self.round_info_label.setText("共 %d 轮" % len(rounds))
        self.round_selector.blockSignals(False)

    def _on_round_selected(self, index):
        round_id = self.round_selector.currentData()
        self._render_view(round_id if round_id is not None else -1)

    def _delete_round(self):
        round_id = self.round_selector.currentData()
        if round_id == -1:
            QMessageBox.warning(self, "提示", "请先选择一个具体轮次")
            return
        reply = QMessageBox.question(
            self, "确认删除", "确定要删除第 %d 轮的记录吗？\n此操作不可恢复。" % round_id,
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.data_mgr.delete_round(round_id)
            self._load_rounds_to_selector()
            self._render_view(-1)
            QMessageBox.information(self, "删除成功", "第 %d 轮记录已删除" % round_id)
