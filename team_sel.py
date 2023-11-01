# Program for manual exploration of team game schedules 
# that allow everyone to play with everyone at least once.

import sys
import math

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QHBoxLayout, \
    QVBoxLayout, QLineEdit, QTableWidget, QTableWidgetItem, QCheckBox, QSplitter, QFrame
from PyQt6.QtGui import QIntValidator, QFontDatabase, QColor
from PyQt6.QtCore import Qt, pyqtSignal

MIN_PLAYER_NUM = 3
MAX_PLAYER_NUM = 100
START_PLAYER_NUM = 10
MIN_TEAM_NUM = 2
START_TEAM_NUM = 2

def int_to_base(num, max_num, base):
    single_digit_length = math.ceil(math.log10(base))
    max_digit_num = math.ceil(math.log(max_num, base))
    digits = []
    while (num > 0):
        digits.append(num % base)
        num //= base
    extra_zeros_num = max_digit_num - len(digits)
    for i in range(extra_zeros_num):
        digits.append(0)
    digits.reverse()
    digits_str = []
    for digit in digits:
        digits_str.append("{0:0{sz}d}".format(digit, sz = single_digit_length))
    return "_".join(digits_str)

class LabeledLimitedLineEdit(QHBoxLayout):
    def __init__(self, text, limits, start_value):
        QHBoxLayout.__init__(self)
        self._text = text
        self.value = start_value
        self._label_obj = QLabel()
        self._edit_obj = QLineEdit("{0}".format(start_value))
        self.addWidget(self._label_obj)
        self.addWidget(self._edit_obj)
        self._edit_obj.textChanged.connect(self._process_text_change)
        self._edit_obj.editingFinished.connect(self._process_value_change)
        self.change_limits(limits)
        self._edit_obj.textChanged.emit(self._edit_obj.text())
    
    def change_limits(self, limits):
        if (limits[1] - limits[0] < 1): # correct limits
            limits[1] = limits[0] + 1
        limits_corr = (limits[0], limits[1] - 1)
        value_corr = int(self._edit_obj.text())
        if (value_corr < limits_corr[0]):
            value_corr = limits_corr[0]
        if (value_corr > limits_corr[1]):
            value_corr = limits_corr[1]
        self.value = value_corr
        self._edit_obj.setText("{0}".format(self.value))
        self._limits = limits_corr
        self._label_obj.setText(self._text.format(self._limits[0], self._limits[1]))
        self._edit_obj.setValidator(None) # delete previous validator
        self._edit_obj.setValidator(QIntValidator(self._limits[0], self._limits[1]))
        self._edit_obj.textChanged.emit(self._edit_obj.text())
        self._process_value_change()
    
    def change_upper_limit(self, upper_limit):
        self.change_limits((self._limits[0], upper_limit))
    
    def _process_value_change(self):
        new_value = int(self._edit_obj.text())
        if (new_value != self.value):
            self.value = new_value
            self.value_changed.emit(self.value)
    
    def _process_text_change(self, new_text):
        if (self._edit_obj.hasAcceptableInput()):
            self._edit_obj.setStyleSheet("border: 1.5px solid #40FF40")
        else:
            self._edit_obj.setStyleSheet("border: 1.5px solid #FF4040")
    
    value_changed = pyqtSignal(int) # isn't emitted if value is not valid

class ScheduleTable(QTableWidget):
    def __init__(self, player_num, team_num):
        QTableWidget.__init__(self)
        self._font_name = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont).family()
        self.setStyleSheet("font-family: {0:s}".format(self._font_name))
        self._default_cell_role = Qt.ItemDataRole.DisplayRole
        self._default_cell_value = ""
        self._round_num = 1
        self._player_num = player_num
        self._team_num = team_num
        self.cellChanged.connect(self._correct_cell)
        self.cellChanged.connect(self._check_for_right_resize)
        self._adjust_size(self._player_num, self._round_num)
        self._update_horz_header()
        self._update_vert_header()
        self.resizeRowsToContents()
        self.resizeColumnsToContents()
    
    def _adjust_size(self, new_row_num, new_col_num):
        self.blockSignals(True)
        old_row_num = self.rowCount()
        old_col_num = self.columnCount()
        if (new_row_num == -1):
            new_row_num = old_row_num
        if (new_col_num == -1):
            new_col_num = old_col_num
        delta_rows = abs(new_row_num - old_row_num)
        delta_cols = abs(new_col_num - old_col_num)

        if (old_row_num > new_row_num):
            for i in range(delta_rows):
                self.removeRow(new_row_num)
        if (old_col_num > new_col_num):
            for i in range(delta_cols):
                self.removeColumn(new_col_num)
        
        if (old_row_num < new_row_num):
            tmp_col_num = self.columnCount()
            for i in range(delta_rows):
                self.insertRow(old_row_num)
                for col in range(tmp_col_num):
                    new_item = QTableWidgetItem()
                    new_item.setData(self._default_cell_role, self._default_cell_value)
                    new_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.setItem(old_row_num, col, new_item)
        if (old_col_num < new_col_num):
            tmp_row_num = self.rowCount()
            for i in range(delta_cols):
                self.insertColumn(old_col_num)
                for row in range(tmp_row_num):
                    new_item = QTableWidgetItem()
                    new_item.setData(self._default_cell_role, self._default_cell_value)
                    new_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.setItem(row, old_col_num, new_item)
        
        self.blockSignals(False)
        self.cellChanged.emit(0, 0)
    
    def change_round_num(self, round_num):
        self._round_num = round_num
        self._adjust_size(-1, self._round_num)
        self._update_horz_header()
        self.resizeRowsToContents()
        self.resizeColumnsToContents()
    
    def change_player_num(self, player_num):
        self._player_num = player_num
        self._adjust_size(self._player_num, -1)
        self._update_vert_header()
        self.resizeRowsToContents()
        self.resizeColumnsToContents()
    
    def change_team_num(self, team_num):
        self._team_num = team_num
        self._update_vert_header()
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                self._correct_cell(row, col)
        self.resizeRowsToContents()
        self.resizeColumnsToContents()
    
    def _update_vert_header(self):
        self.setVerticalHeaderLabels(\
            ["Player {0:0{sz}d} | {1:s}".format(i, int_to_base(i, self._player_num, self._team_num), \
                sz = math.floor(math.log10(self._player_num - 1)) + 1) \
                for i in range(self._player_num)])
    
    def _update_horz_header(self):
        self.setHorizontalHeaderLabels(\
            ["Round {0:d}".format(i + 1) for i in range(self._round_num)])
    
    def _check_for_right_resize(self, row, col):
        # only checks the rightmost column, so can't delete several at the same time
        item = self.item(row, col)
        value = item.data(self._default_cell_role)

        if ((value == "") and (col == self.columnCount() - 2)):
            col_empty = True
            for cur_row in range(self.rowCount()):
                cur_item = self.item(cur_row, col)
                cur_value = cur_item.data(self._default_cell_role)
                if (not (cur_value == "")):
                    col_empty = False
                    break
            if (col_empty):
                self.change_round_num(self._round_num - 1)
        
        if ((value != "") and (col == self.columnCount() - 1)):
            col_started = True
            for cur_row in range(self.rowCount()):
                if (cur_row == row):
                    continue
                cur_item = self.item(cur_row, col)
                cur_value = cur_item.data(self._default_cell_role)
                if (not (cur_value == "")):
                    col_started = False
                    break
            if (col_started):
                self.change_round_num(self._round_num + 1)
        
        self.resizeRowsToContents()
        self.resizeColumnsToContents()
    
    def _correct_cell(self, row, col):
        item = self.item(row, col)
        value = item.data(self._default_cell_role)
        if (value == ""):
            new_value = ""
        else:
            try:
                new_value = int(value)
            except Exception:
                new_value = 0
            if (new_value < 0):
                new_value = 0
            if (new_value >= self._team_num):
                new_value = self._team_num - 1
            new_value = "{0:0{sz}d}".format(new_value, \
                sz = math.ceil(math.log10(self._team_num)))
        item.setData(self._default_cell_role, new_value)
        self.resizeRowsToContents()
        self.resizeColumnsToContents()
    
    def get_schedule(self):
        rows = self.rowCount()
        cols = self.columnCount() - 1
        if (cols == 0): # fix the case of all empty (= all zeros) first column
            cols = 1
        tbl_data = []
        for row in range(rows):
            row_data = []
            for col in range(cols):
                item = self.item(row, col)
                value = item.data(self._default_cell_role)
                if (value == ""):
                    value = 0
                else:
                    value = int(value)
                row_data.append(value)
            tbl_data.append(row_data)
        return tbl_data

class ResultsTable(QTableWidget):
    def __init__(self):
        QTableWidget.__init__(self)
        self._font_name = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont).family()
        self.setStyleSheet("font-family: {0:s}".format(self._font_name))
        self._default_cell_role = Qt.ItemDataRole.DisplayRole
        self._default_cell_value = ""
        self._cell_add_value_on = "■"
        self._cell_add_value_off = "□"
        self._color_filled = QColor(0, 255, 0, 63)
        self._color_not_filled = QColor(255, 0, 0, 63)
    
    def set_schedule(self, schedule):
        players = len(schedule)
        if (players > 0):
            rounds = len(schedule[0])
        else:
            rounds = 0
        self.clear()
        self.setRowCount(players)
        self.setColumnCount(players)
        header = ["{0:d}".format(i) for i in range(players)]
        self.setVerticalHeaderLabels(header)
        self.setHorizontalHeaderLabels(header)

        for row in range(players):
            for col in range(players):
                new_item = QTableWidgetItem()
                new_item.setData(self._default_cell_role, self._default_cell_value)
                new_item_flags = new_item.flags()
                new_item_flags &= ~Qt.ItemFlag.ItemIsEditable
                new_item.setFlags(new_item_flags)
                new_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.setItem(row, col, new_item)
        
        for cur_round in range(rounds): # handles "rounds == 0" as well
            player_pairs = set()
            player_teams = [schedule[i][cur_round] for i in range(players)]
            for (player_1, player_1_team) in enumerate(player_teams):
                for (player_2, player_2_team) in enumerate(player_teams):
                    if (player_1_team == player_2_team):
                        player_pairs.add((player_1, player_2))
            for row in range(players):
                for col in range(players):
                    if ((row, col) in player_pairs):
                        add_value = self._cell_add_value_on
                    else:
                        add_value = self._cell_add_value_off
                    item = self.item(row, col)
                    value = item.data(self._default_cell_role)
                    new_value = "".join([value, add_value])
                    item.setData(self._default_cell_role, new_value)
        
        for row in range(players):
            for col in range(players):
                item = self.item(row, col)
                value = item.data(self._default_cell_role)
                if (value.find(self._cell_add_value_on) >= 0):
                    cur_color = self._color_filled
                else:
                    cur_color = self._color_not_filled
                item.setBackground(cur_color)
        
        self.resizeRowsToContents()
        self.resizeColumnsToContents()

class TeamSelMainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self._layout_edits = QVBoxLayout()
        self._llle_player_num = LabeledLimitedLineEdit(\
            "Player number ({0} - {1}): ", (MIN_PLAYER_NUM, MAX_PLAYER_NUM), START_PLAYER_NUM)
        self._layout_edits.addLayout(self._llle_player_num)
        self._llle_team_num = LabeledLimitedLineEdit(\
            "Team number ({0} - {1}): ", (MIN_TEAM_NUM, START_PLAYER_NUM), START_TEAM_NUM)
        self._layout_edits.addLayout(self._llle_team_num)

        # connect two "edits" above: team_num < player_num
        self._llle_player_num.value_changed.connect(self._llle_team_num.change_upper_limit)
        self._llle_player_num.value_changed.emit(START_PLAYER_NUM)

        self._layout_params = QVBoxLayout()
        self._layout_params.addLayout(self._layout_edits)
        self._label_schedule = QLabel("Schedule (input teams, empty = 0)")
        self._layout_params.addWidget(self._label_schedule)
        self._st_schedule = ScheduleTable(self._llle_player_num.value, self._llle_team_num.value)
        self._llle_player_num.value_changed.connect(self._st_schedule.change_player_num)
        self._llle_team_num.value_changed.connect(self._st_schedule.change_team_num)
        self._layout_params.addWidget(self._st_schedule)
        self._checkbox_calculate = QCheckBox("(Re)Calculate")
        self._checkbox_calculate.stateChanged.connect(self._checkbox_calculate_state_change)
        self._layout_params.addWidget(self._checkbox_calculate)

        self._layout_results = QVBoxLayout()
        self._label_results = QLabel("Results (player with player)")
        self._layout_results.addWidget(self._label_results)
        self._rt_results = ResultsTable()
        self._layout_results.addWidget(self._rt_results)

        self._widget_params = QFrame()
        self._widget_params.setLayout(self._layout_params)
        self._widget_results = QFrame()
        self._widget_results.setLayout(self._layout_results)

        self._splitter_main = QSplitter()
        self._splitter_main.addWidget(self._widget_params)
        self._splitter_main.addWidget(self._widget_results)

        self.resize(1024, 640)
        self.setWindowTitle("Team selection experiment")
        self.setCentralWidget(self._splitter_main)
    
    def _checkbox_calculate_state_change(self, state):
        if (state == Qt.CheckState.Unchecked.value):
            self._st_schedule.cellChanged.disconnect(self._recalculate_action)
        if (state == Qt.CheckState.Checked.value):
            self._recalculate_action()
            self._st_schedule.cellChanged.connect(self._recalculate_action)
    
    def _recalculate_action(self):
        schedule = self._st_schedule.get_schedule()
        self._rt_results.set_schedule(schedule)

app = QApplication(sys.argv)
main_window = TeamSelMainWindow()
main_window.show()
sys.exit(app.exec())
