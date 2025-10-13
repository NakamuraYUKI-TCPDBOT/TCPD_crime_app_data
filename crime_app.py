import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QGridLayout,
    QCheckBox, QPushButton, QLabel, QLineEdit, QScrollArea,
    QSpacerItem, QSizePolicy, QHBoxLayout
)
from PyQt5.QtCore import Qt
import json
from functools import partial

# crimes.jsonの読み込み
with open('crimes.json', encoding='utf-8') as f:
    crimes = json.load(f)

# groups.jsonの読み込み
with open('groups.json', encoding='utf-8') as f:
    groups = json.load(f)

# buttons.jsonの読み込み
with open('buttons.json', encoding='utf-8') as f:
    buttons = json.load(f)

class CrimeApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Turtle City 警察用 罰金計算アプリ')
        self.resize(690, 900)

        # メインレイアウト
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        # スクロール用ウィジェットとレイアウト
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        self.checkboxes = []
        self.input_counts = []
        self.input_fines = []
        self.input_prisons = []

        # グリッドレイアウトで列を揃える
        grid = QGridLayout()
        header_labels = ["罪状名", "罰金", "プリズン", "個数/金額", "時間"]
        for col, text in enumerate(header_labels):
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignCenter)
            grid.addWidget(lbl, 0, col)

        # 列幅調整
        grid.setColumnMinimumWidth(0, 200)  # 罪状名
        grid.setColumnMinimumWidth(1, 100)  # 罰金
        grid.setColumnMinimumWidth(2, 100)  # プリズン
        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        grid.setColumnStretch(3, 1)
        grid.setColumnStretch(4, 1)

        for idx, crime in enumerate(crimes):
            cb = QCheckBox(crime['name'])
            cb.stateChanged.connect(self.calc_total)
            self.checkboxes.append(cb)
            grid.addWidget(cb, idx+1, 0)

            fine_label = QLabel(f"{crime.get('fine', 0)//1}万")
            fine_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(fine_label, idx+1, 1)

            prison_label = QLabel(f"{crime.get('prison', 0)}分")
            prison_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(prison_label, idx+1, 2)

            # --- 個数・金額入力欄をまとめて横並びに ---
            input_widget = QWidget()
            input_layout = QHBoxLayout(input_widget)
            input_layout.setContentsMargins(0, 0, 0, 0)

            # 個数入力
            if crime.get("input_count", False):
                le_count = QLineEdit("")
                le_count.setFixedWidth(60)
                le_count.setAlignment(Qt.AlignRight)
                le_count.setPlaceholderText(crime.get("input_count_label", "個数"))
                le_count.textChanged.connect(partial(self.on_input_changed, idx))
                input_layout.addWidget(le_count)
                self.input_counts.append(le_count)
            else:
                self.input_counts.append(None)

            # 金額入力
            if crime.get("input_fine", False):
                le_fine = QLineEdit("")
                le_fine.setFixedWidth(100)
                le_fine.setAlignment(Qt.AlignRight)
                le_fine.setPlaceholderText(crime.get("input_fine_label", "金額"))
                le_fine.textChanged.connect(partial(self.on_input_changed, idx))
                input_layout.addWidget(le_fine)
                self.input_fines.append(le_fine)
            else:
                self.input_fines.append(None)

            # まとめてグリッドの3列目に追加
            grid.addWidget(input_widget, idx+1, 3)

            # --- 時間入力 ---
            if crime.get("input_prison", False):
                le_prison = QLineEdit("")
                le_prison.setFixedWidth(100)
                le_prison.setAlignment(Qt.AlignRight)
                le_prison.setPlaceholderText(crime.get("input_prison_label", "時間"))
                le_prison.textChanged.connect(partial(self.on_input_changed, idx))
                grid.addWidget(le_prison, idx+1, 4)
                self.input_prisons.append(le_prison)
            else:
                empty = QLabel("")
                empty.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                grid.addWidget(empty, idx+1, 4)
                self.input_prisons.append(None)

        scroll_layout.addLayout(grid)

        # 合計表示
        self.total_label = QLabel("合計罰金額: 0万, 合計プリズン時間: 0分")
        self.total_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        scroll_layout.addWidget(self.total_label)

        # 特殊ボタン
        btn_widget = QWidget()
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(12)

        btn_copy_incident = QPushButton("インシデントコピー")
        btn_copy_incident.setStyleSheet("font-size: 15px;")
        btn_copy_incident.clicked.connect(self.copy_incident)
        btn_layout.addWidget(btn_copy_incident)

        btn_copy_fine = QPushButton("罰金金額コピー")
        btn_copy_fine.setStyleSheet("font-size: 15px;")
        btn_copy_fine.clicked.connect(self.copy_fine)
        btn_layout.addWidget(btn_copy_fine)

        scroll_layout.addWidget(btn_widget)


        # --- QGridLayoutでボタンを複数段に配置 ---
        btn_grid = QGridLayout()
        buttons_per_row = 5
        group_colors = {
            "小型": "background-color: #ffe066; color: black;",
            "中型": "background-color: #b3e6ff; color: black;",
            "大型": "background-color: #ffb3b3; color: black;",
            "特殊": "background-color: #ffb3b3; color: black;",
            "操作": "background-color: #cccccc; color: black;",
        }

        row = 0
        col = 0
        current_group = None
        for btn_info in buttons:
            label = btn_info["label"]
            group_names = btn_info.get("group_names", [])
            group = btn_info.get("group", "")
            clear_first = btn_info.get("clear_first", False)
            is_clear = btn_info.get("is_clear", False)

            if group != current_group and current_group is not None:
                spacer = QSpacerItem(0, 16, QSizePolicy.Minimum, QSizePolicy.Fixed)
                btn_grid.addItem(spacer, row, 0, 1, buttons_per_row)
                row += 1
                col = 0
            current_group = group

            btn = QPushButton(label)
            if group in group_colors:
                btn.setStyleSheet(group_colors[group])

            if is_clear:
                btn.clicked.connect(self.clear_all)
            else:
                if clear_first:
                    btn.clicked.connect(lambda _, g=group_names: self.clear_and_check_group(g))
                else:
                    btn.clicked.connect(lambda _, g=group_names: self.check_group(g))

            btn_grid.addWidget(btn, row, col)
            col += 1
            if col >= buttons_per_row:
                row += 1
                col = 0

        scroll_layout.addLayout(btn_grid)

        # スクロールエリアにセット（1回だけ！）
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)

    def calc_total(self):
        total_fine = 0
        normal_prison = 0
        over_prison = 0
        for idx, cb in enumerate(self.checkboxes):
            if cb.isChecked():
                crime = crimes[idx]
                fine = crime.get("fine", 0)
                prison = crime.get("prison", 0)
                # 個数入力
                if self.input_counts[idx] is not None:
                    try:
                        count = int(self.input_counts[idx].text())
                    except:
                        count = 0
                    fine += crime.get("fine_per_unit", 0) * count
                    prison += crime.get("prison_per_unit", 0) * count
                # 金額手動入力
                if self.input_fines[idx] is not None:
                    try:
                        fine += int(self.input_fines[idx].text()) * 1
                    except:
                        pass
                # 時間手動入力
                if self.input_prisons[idx] is not None:
                    try:
                        prison += int(self.input_prisons[idx].text())
                    except:
                        pass
                total_fine += fine
                if crime.get("allow_prison_over", False):
                    over_prison += prison
                else:
                    normal_prison += prison
        total_prison = min(normal_prison, 60) + over_prison
        self.total_label.setText(
            f"合計罰金額: {total_fine // 1}万, 合計プリズン時間: {total_prison}分"
        )


    def check_group(self, group_names):
        if isinstance(group_names, str):
            group_names = [group_names]
        checked_indices = set()
        for group_name in group_names:
            checked_indices.update(groups.get(group_name, []))
        for idx in checked_indices:
            self.checkboxes[idx].setChecked(True)
        self.calc_total()

    def clear_all(self):
        for cb in self.checkboxes:
            cb.setChecked(False)
        for inp in self.input_counts + self.input_fines + self.input_prisons:
            if inp is not None:
                inp.setText("")
        self.calc_total()

    def clear_and_check_group(self, group_names):
        self.clear_all()
        self.check_group(group_names)

    def on_input_changed(self, idx):
        # 入力欄が空でなければチェックボックスをON
        checked = False
        if self.input_counts[idx] is not None and self.input_counts[idx].text().strip():
            checked = True
        if self.input_fines[idx] is not None and self.input_fines[idx].text().strip():
            checked = True
        if self.input_prisons[idx] is not None and self.input_prisons[idx].text().strip():
            checked = True

        if checked:
            self.checkboxes[idx].setChecked(True)
        self.calc_total()

    def copy_incident(self):
        # チェックがついた罪状名を「、」区切りでクリップボードにコピー
        names = [cb.text() for cb in self.checkboxes if cb.isChecked()]
        text = "、".join(names)
        QApplication.clipboard().setText(text)

    def copy_fine(self):
        # 合計罰金額を1円単位でクリップボードにコピー
        total_fine = 0
        for idx, cb in enumerate(self.checkboxes):
            if cb.isChecked():
                crime = crimes[idx]
                fine = crime.get("fine", 0)
                # 個数入力
                if self.input_counts[idx] is not None:
                    try:
                        count = int(self.input_counts[idx].text())
                    except:
                        count = 0
                    fine += crime.get("fine_per_unit", 0) * count
                # 金額手動入力
                if self.input_fines[idx] is not None:
                    try:
                        fine += int(self.input_fines[idx].text())
                    except:
                        pass
                total_fine += fine
        # 万単位→円単位
        yen = int(total_fine * 10000)
        QApplication.clipboard().setText(str(yen))



if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = CrimeApp()
    win.show()
    sys.exit(app.exec_())
