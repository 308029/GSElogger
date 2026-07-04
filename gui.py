import sys
import os
import pandas
import pyqtgraph as pg
import tempfile
import shutil
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QFormLayout, QLineEdit, QPushButton, QComboBox, QFileDialog,
                             QMessageBox, QLabel, QDialog, QListWidget, QListWidgetItem, QSplitter,
                             QProgressDialog)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QSize

# リファクタリング後の解析モジュールをインポート
from raw_converter import RawDataConverter
from thrust_analyzer import ThrustAnalyzer
from graph_generator import GraphGenerator

class ImageViewerDialog(QDialog):
    def __init__(self, image_paths_dict, out_dir, parent=None):
        super().__init__(parent)
        self.out_dir = out_dir
        self.original_pixmap = None

        self.setWindowTitle("グラフプレビュー")
        self.resize(1000, 700)

        # Main layout
        layout = QVBoxLayout(self)
        
        # Splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel (list of images)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0,0,0,0)
        
        left_layout.addWidget(QLabel("保存する画像を選択:"))

        # 全て選択 / 選択解除ボタン
        select_all_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("全て選択")
        self.select_all_btn.clicked.connect(self.select_all_images)
        self.deselect_all_btn = QPushButton("全て選択解除")
        self.deselect_all_btn.clicked.connect(self.deselect_all_images)
        select_all_layout.addWidget(self.select_all_btn)
        select_all_layout.addWidget(self.deselect_all_btn)
        left_layout.addLayout(select_all_layout)

        self.list_widget = QListWidget()
        
        for category, paths in image_paths_dict.items():
            if not paths: continue
            # セクション見出し
            section_item = QListWidgetItem(f"【 {category} 】")
            section_item.setFlags(Qt.ItemFlag.NoItemFlags) # 選択・チェック不可
            self.list_widget.addItem(section_item)
            
            for path in paths:
                item = QListWidgetItem(f"  {os.path.basename(path)}")
                item.setData(Qt.ItemDataRole.UserRole, path) # 元のパスを保存
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.list_widget.addItem(item)
                
        self.list_widget.currentItemChanged.connect(self.update_preview)
        left_layout.addWidget(self.list_widget)
        
        splitter.addWidget(left_widget)

        # Right panel (image preview)
        self.image_label = QLabel("リストから画像を選択してください")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        splitter.addWidget(self.image_label)
        
        splitter.setSizes([250, 750]) # Initial size ratio
        layout.addWidget(splitter)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("選択した画像を保存して閉じる")
        self.save_btn.clicked.connect(self.save_and_close)
        btn_layout.addWidget(self.save_btn)

        self.close_btn = QPushButton("破棄して閉じる")
        self.close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)

        # 最初のチェック可能なアイテムを選択
        for i in range(self.list_widget.count()):
            if self.list_widget.item(i).flags() & Qt.ItemFlag.ItemIsUserCheckable:
                self.list_widget.setCurrentRow(i)
                break

    def update_preview(self, current, previous):
        if not current or not current.flags() & Qt.ItemFlag.ItemIsUserCheckable:
            self.image_label.clear()
            self.image_label.setText("リストから画像を選択してください")
            self.original_pixmap = None
            return

        path_to_show = current.data(Qt.ItemDataRole.UserRole)

        if path_to_show and os.path.exists(path_to_show):
            self.original_pixmap = QPixmap(path_to_show)
            self.scale_and_set_pixmap()
        else:
            self.image_label.setText(f"画像が見つかりません")
            self.original_pixmap = None

    def scale_and_set_pixmap(self):
        if self.original_pixmap and not self.original_pixmap.isNull():
            dpr = self.devicePixelRatioF()
            label_size = self.image_label.size()
            target_size = QSize(int(label_size.width() * dpr), int(label_size.height() * dpr))

            scaled_pixmap = self.original_pixmap.scaled(
                target_size, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            scaled_pixmap.setDevicePixelRatio(dpr)
            self.image_label.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.scale_and_set_pixmap()
        
    def showEvent(self, event):
        super().showEvent(event)
        self.scale_and_set_pixmap()

    def select_all_images(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                item.setCheckState(Qt.CheckState.Checked)

    def deselect_all_images(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                item.setCheckState(Qt.CheckState.Unchecked)

    def save_and_close(self):
        saved_count = 0
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                if item.checkState() == Qt.CheckState.Checked:
                    src_path = item.data(Qt.ItemDataRole.UserRole)
                    if src_path:
                        try:
                            shutil.copy(src_path, self.out_dir)
                            saved_count += 1
                        except Exception as e:
                            QMessageBox.warning(self, "保存エラー", f"ファイルの保存に失敗しました:\n{src_path}\n\nエラー: {e}")
                            return # Stop on first error
        
        if saved_count > 0:
            QMessageBox.information(self, "保存完了", f"{saved_count}個の画像を保存しました。")
        
        self.accept()

class ThrustAnalyzerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.preview_df = None
        self.current_rawfile = ""
        self.current_loadcell = None
        self.current_loggertype = ""
        self.is_burn_line_visible = False
        self.is_zoomed_to_selection = False
        self.temp_dir = None
        self.image_paths_dict = {}
        self.analyzed_df = None
        self.onlythurst_df = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('ロガー結果 解析GUI')
        self.resize(1000, 600)

        main_layout = QHBoxLayout()
        
        # 左側の設定用レイアウト
        left_widget = QWidget()
        layout = QVBoxLayout(left_widget)

        # Raw File
        layout.addWidget(QLabel("Rawデータファイル (CSV):"))
        rawfile_layout = QHBoxLayout()
        self.rawfile_input = QLineEdit()
        self.rawfile_btn = QPushButton("参照")
        self.rawfile_btn.clicked.connect(self.browse_rawfile)
        rawfile_layout.addWidget(self.rawfile_input)
        rawfile_layout.addWidget(self.rawfile_btn)
        layout.addLayout(rawfile_layout)

        # その他の設定1 (ロードセル・ロガータイプ)
        form_layout1 = QFormLayout()

        # Loadcell Max LBF
        self.loadcell_combo = QComboBox()
        self.loadcell_combo.addItems(["500", "250", "1000"])
        form_layout1.addRow("ロードセル最大推力:", self.loadcell_combo)

        # Logger Type
        self.loggertype_combo = QComboBox()
        self.loggertype_combo.addItems(["new", "old"])
        form_layout1.addRow("ロガータイプ:", self.loggertype_combo)

        # Preview Column Selection
        self.preview_col_combo = QComboBox()
        self.preview_col_combo.addItems(["推力[N]", "圧力1[Pa]", "圧力2[Pa]", "圧力3[Pa]", "圧力4[Pa]"])
        self.preview_col_combo.currentTextChanged.connect(self.preview_col_changed)
        form_layout1.addRow("プレビュー対象:", self.preview_col_combo)
        
        layout.addLayout(form_layout1)

        # Preview Buttons
        preview_layout = QHBoxLayout()
        self.show_all_btn = QPushButton("全体を表示")
        self.show_all_btn.clicked.connect(self.show_all_graph)
        preview_layout.addWidget(self.show_all_btn)

        self.show_select_btn = QPushButton("選択範囲を表示")
        self.show_select_btn.clicked.connect(self.show_selected_region)
        preview_layout.addWidget(self.show_select_btn)

        self.show_burn_btn = QPushButton("燃焼終了を表示")
        self.show_burn_btn.clicked.connect(self.show_burn_end_line)
        preview_layout.addWidget(self.show_burn_btn)

        layout.addLayout(preview_layout)

        # その他の設定2 (時間情報)
        form_layout2 = QFormLayout()

        # Start Time (Manual mode settings)
        self.starttime_input = QLineEdit()
        self.starttime_input.setPlaceholderText("指定しない場合は空欄")
        form_layout2.addRow("開始時間:", self.starttime_input)

        # End Time (Manual mode settings)
        self.endtime_input = QLineEdit()
        self.endtime_input.setPlaceholderText("指定しない場合は空欄")
        form_layout2.addRow("終了時間 (作動終了):", self.endtime_input)

        # Burn End Time (Manual mode settings)
        self.burn_endtime_input = QLineEdit()
        self.burn_endtime_input.setPlaceholderText("指定しない場合は空欄")
        form_layout2.addRow("燃焼終了時間:", self.burn_endtime_input)

        layout.addLayout(form_layout2)

        # ステータス表示用ラベル
        self.status_label = QLabel("ステータス: 待機中")
        self.status_label.setStyleSheet("font-weight: bold; color: #555555; padding: 2px;")
        layout.addWidget(self.status_label)

        # 解析結果表示用ラベル
        self.result_label = QLabel(
            "【解析結果】\n"
            "定常偏差: -\n"
            "燃焼時間: -\n"
            "作動時間: -\n"
            "燃焼時間平均推力: -\n"
            "最大推力 (補正前): -\n"
            "最大推力 (補正後): -\n"
            "燃焼時間トータルインパルス: -\n"
            "作動時間トータルインパルス: -"
        )
        self.result_label.setStyleSheet("padding: 10px; border: 1px solid #ccc; background-color: #f9f9f9; color: black; font-weight: bold;")
        layout.addWidget(self.result_label)

        # Output Directory を解析実行ボタンの上に移動
        layout.addWidget(QLabel("出力先フォルダ:"))
        outdir_layout = QHBoxLayout()
        self.outdir_input = QLineEdit()
        self.outdir_btn = QPushButton("参照")
        self.outdir_btn.clicked.connect(self.browse_outdir)
        outdir_layout.addWidget(self.outdir_input)
        outdir_layout.addWidget(self.outdir_btn)
        layout.addLayout(outdir_layout)

        # Run / Refer Buttons Layout
        run_layout = QHBoxLayout()
        self.run_btn = QPushButton("解析を実行")
        self.run_btn.setStyleSheet("font-weight: bold; padding: 10px;")
        self.run_btn.clicked.connect(self.run_analysis)
        self.run_btn.setEnabled(False) # 初期状態は無効
        run_layout.addWidget(self.run_btn)

        self.refer_btn = QPushButton("過去の解析を参照")
        self.refer_btn.setStyleSheet("font-weight: bold; padding: 10px;")
        self.refer_btn.clicked.connect(self.refer_past_analysis)
        run_layout.addWidget(self.refer_btn)
        
        layout.addLayout(run_layout)

        # CSV出力ボタン（初期状態は無効）
        self.save_csv_btn = QPushButton("解析結果データをCSV出力")
        self.save_csv_btn.setStyleSheet("font-weight: bold; padding: 10px;")
        self.save_csv_btn.setEnabled(False)
        self.save_csv_btn.clicked.connect(self.export_csv)
        layout.addWidget(self.save_csv_btn)

        # 画像表示ボタン（初期状態は無効）
        self.show_images_btn = QPushButton("生成された画像を表示 / 保存")
        self.show_images_btn.setStyleSheet("font-weight: bold; padding: 10px;")
        self.show_images_btn.setEnabled(False)
        self.show_images_btn.clicked.connect(self.show_images)
        layout.addWidget(self.show_images_btn)

        main_layout.addWidget(left_widget, 1)

        # 右側のグラフ描画用レイアウト
        self.plot_widget = pg.PlotWidget(title="推力データ プレビュー")
        self.plot_widget.setLabel('bottom', 'データ取得開始時 [s]')
        self.plot_widget.setLabel('left', '推力[N]')
        self.plot_widget.showGrid(x=True, y=True)
        
        self.region = pg.LinearRegionItem()
        self.region.setZValue(10)
        self.region.setMovable(False)          # 中央領域のドラッグによる全体移動を無効化
        self.region.lines[0].setMovable(True)  # 左の境界線のみドラッグ可能に
        self.region.lines[1].setMovable(True)  # 右の境界線のみドラッグ可能に
        self.region.sigRegionChanged.connect(self.update_region)
        main_layout.addWidget(self.plot_widget, 2)
        
        # 燃焼終了時間用の赤いライン
        self.burn_line = pg.InfiniteLine(angle=90, movable=True, pen=pg.mkPen('r', width=2))
        self.burn_line.setZValue(15)
        self.burn_line.sigPositionChanged.connect(self.update_burn_line)
        self.burn_line.hide()  # 最初は非表示

        # カーソル位置表示用のクロスヘアとラベル
        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('gray', style=Qt.PenStyle.DashLine))
        self.hLine = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('gray', style=Qt.PenStyle.DashLine))
        self.plot_widget.addItem(self.vLine, ignoreBounds=True)
        self.plot_widget.addItem(self.hLine, ignoreBounds=True)
        
        self.cursor_label = pg.TextItem(anchor=(0, 1), fill=(255, 255, 255, 200))
        self.plot_widget.addItem(self.cursor_label, ignoreBounds=True)
        
        self.proxy = pg.SignalProxy(self.plot_widget.scene().sigMouseMoved, rateLimit=60, slot=self.mouse_moved)

        # 時間入力欄が変更されたら解析ボタンの有効/無効を判定する
        self.starttime_input.textChanged.connect(self.check_run_btn_state)
        self.endtime_input.textChanged.connect(self.check_run_btn_state)
        self.burn_endtime_input.textChanged.connect(self.check_run_btn_state)

        # 時間入力欄の編集完了時にグラフに反映する
        self.starttime_input.editingFinished.connect(self.manual_update_region)
        self.endtime_input.editingFinished.connect(self.manual_update_region)
        self.burn_endtime_input.editingFinished.connect(self.manual_update_burn_line)

        self.setLayout(main_layout)

    def mouse_moved(self, evt):
        pos = evt[0]
        if self.plot_widget.sceneBoundingRect().contains(pos):
            mousePoint = self.plot_widget.plotItem.vb.mapSceneToView(pos)
            x_val = mousePoint.x()
            self.vLine.setPos(x_val)
            
            y_val = mousePoint.y()
            if self.preview_df is not None and not self.preview_df.empty:
                x_val_us = x_val * 1000000.0
                x_data = self.preview_df["データ取得開始時"].values
                selected_col = self.preview_col_combo.currentText()
                if selected_col in self.preview_df.columns:
                    y_data = self.preview_df[selected_col].values
                    if x_val_us <= x_data[0]:
                        y_val = y_data[0]
                    elif x_val_us >= x_data[-1]:
                        y_val = y_data[-1]
                    else:
                        idx = self.preview_df["データ取得開始時"].searchsorted(x_val_us)
                        if idx > 0 and idx < len(x_data):
                            if abs(x_data[idx] - x_val_us) < abs(x_data[idx-1] - x_val_us):
                                y_val = y_data[idx]
                            else:
                                y_val = y_data[idx-1]
                            
            self.hLine.setPos(y_val)
            self.cursor_label.setPos(x_val, y_val)
            selected_col = self.preview_col_combo.currentText()
            unit = "N" if "推力" in selected_col else "Pa"
            self.cursor_label.setHtml(f"<div style='text-align: left;'><span style='color: black; font-size: 10pt; font-weight: bold;'>時間: {x_val:.3f} s<br>{selected_col}: {y_val:.2f} {unit}</span></div>")

    def check_run_btn_state(self):
        if (self.starttime_input.text().strip() and 
            self.endtime_input.text().strip() and 
            self.burn_endtime_input.text().strip()):
            self.run_btn.setEnabled(True)
        else:
            self.run_btn.setEnabled(False)

    def browse_rawfile(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Rawデータファイルを選択", "", "CSVファイル (*.csv);;すべてのファイル (*)")
        if file_path:
            self.rawfile_input.setText(file_path)
            if not self.outdir_input.text():
                # 生データと同じディレクトリ内に out フォルダを作るように初期設定
                self.outdir_input.setText(os.path.join(os.path.dirname(file_path), "out"))

    def browse_outdir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "出力先フォルダを選択")
        if dir_path:
            self.outdir_input.setText(dir_path)

    def ensure_data_loaded(self):
        abrawfile = self.rawfile_input.text()
        aboutdir = self.outdir_input.text()
        loadcell_max_lbf = int(self.loadcell_combo.currentText())
        loggertype = self.loggertype_combo.currentText()

        if not abrawfile or not os.path.exists(abrawfile):
            QMessageBox.warning(self, "エラー", "Rawデータファイルを選択してください。")
            return False

        os.makedirs(aboutdir, exist_ok=True)
        abredatafile = os.path.join(aboutdir, "converted.csv")

        # ファイルや設定が変わったか、まだデータを読み込んでいない場合は変換・読み込みを行う
        need_convert = False
        if (self.current_rawfile != abrawfile or 
            self.current_loadcell != loadcell_max_lbf or
            self.current_loggertype != loggertype or
            self.preview_df is None):
            need_convert = True

        if need_convert:
            self.show_all_btn.setEnabled(False)
            self.show_select_btn.setEnabled(False)
            self.show_burn_btn.setEnabled(False)
            old_text = self.sender().text() if self.sender() else "処理中..."
            if self.sender():
                self.sender().setText("変換中...")
            self.status_label.setText("ステータス: データ変換中...")
            self.status_label.setStyleSheet("font-weight: bold; color: #d4a373; padding: 2px;")
            QApplication.processEvents()

            try:
                RawDataConverter(abrawfile, abredatafile, loadcell_max_lbf, loggertype).convert()
                self.preview_df = pandas.read_csv(abredatafile)
                self.current_rawfile = abrawfile
                self.current_loadcell = loadcell_max_lbf
                self.current_loggertype = loggertype
                
                self.replot_graph()
                
                # 初期値の自動計算を設定する
                min_x, max_x = self.preview_df["データ取得開始時"].min(), self.preview_df["データ取得開始時"].max()
                try:
                    preview_logger = ThrustAnalyzer(abredatafile, aboutdir, "データ取得開始時", "推力[N]")
                    auto_start = preview_logger.burn_start_time
                    auto_end = preview_logger.operation_end_time
                    auto_burn_end = auto_start + (preview_logger.burn_end_time * 1000000.0)
                except Exception:
                    auto_start = min_x
                    auto_end = max_x
                    auto_burn_end = min_x + (max_x - min_x) * 0.5
                
                if not (min_x <= auto_start <= max_x) or not (min_x <= auto_end <= max_x) or auto_start >= auto_end:
                    auto_start, auto_end = min_x, max_x
                if not (min_x <= auto_burn_end <= max_x):
                    auto_burn_end = min_x + (max_x - min_x) * 0.5

                auto_start_sec = auto_start / 1000000.0
                auto_end_sec = auto_end / 1000000.0
                auto_burn_end_sec = auto_burn_end / 1000000.0

                self.region.setRegion([auto_start_sec, auto_end_sec])
                self.burn_line.setPos(auto_burn_end_sec)
                
                self.status_label.setText("ステータス: プレビュー表示完了")
                self.status_label.setStyleSheet("font-weight: bold; color: green; padding: 2px;")
                
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"プレビュー生成中にエラーが発生しました:\n{str(e)}")
                return False
            finally:
                self.show_all_btn.setEnabled(True)
                self.show_select_btn.setEnabled(True)
                self.show_burn_btn.setEnabled(True)
                if self.sender():
                    self.sender().setText(old_text)
        return True

    def replot_graph(self):
        if self.preview_df is None or self.preview_df.empty:
            return
            
        selected_col = self.preview_col_combo.currentText()
        if selected_col not in self.preview_df.columns:
            return
            
        self.plot_widget.clear()
        self.plot_widget.addItem(self.region)
        self.plot_widget.addItem(self.burn_line)
        self.plot_widget.addItem(self.vLine, ignoreBounds=True)
        self.plot_widget.addItem(self.hLine, ignoreBounds=True)
        self.plot_widget.addItem(self.cursor_label, ignoreBounds=True)
        
        if not self.is_burn_line_visible:
            self.burn_line.hide()
        else:
            self.burn_line.show()
            
        self.plot_widget.plot(self.preview_df["データ取得開始時"].values / 1000000.0, self.preview_df[selected_col].values, pen='c')
        self.plot_widget.setLabel('bottom', 'データ取得開始時 [s]')
        self.plot_widget.setLabel('left', selected_col)
        self.plot_widget.setTitle(f"{selected_col} プレビュー")

    def preview_col_changed(self):
        if self.preview_df is None or self.preview_df.empty:
            return
        self.replot_graph()
        # Keep currently zoomed view but update Y range
        x_min, x_max = self.plot_widget.viewRange()[0]
        st_us = x_min * 1000000.0
        et_us = x_max * 1000000.0
        selected_col = self.preview_col_combo.currentText()
        mask = (self.preview_df["データ取得開始時"] >= st_us) & (self.preview_df["データ取得開始時"] <= et_us)
        if mask.any():
            local_max_y = self.preview_df.loc[mask, selected_col].max()
            self.plot_widget.setYRange(0, local_max_y * 1.1, padding=0)

    def show_all_graph(self):
        if not self.ensure_data_loaded():
            return
            
        min_x_sec = self.preview_df["データ取得開始時"].min() / 1000000.0
        max_x_sec = self.preview_df["データ取得開始時"].max() / 1000000.0
        
        self.plot_widget.setXRange(min_x_sec, max_x_sec, padding=0)
        selected_col = self.preview_col_combo.currentText()
        max_y = self.preview_df[selected_col].max()
        self.plot_widget.setYRange(0, max_y * 1.1, padding=0)
        self.is_zoomed_to_selection = False

    def show_selected_region(self):
        if not self.ensure_data_loaded():
            return
            
        st_text = self.starttime_input.text().strip()
        et_text = self.endtime_input.text().strip()
        if not st_text or not et_text:
            # Auto-calculate range
            min_x = self.preview_df["データ取得開始時"].min()
            max_x = self.preview_df["データ取得開始時"].max()
            try:
                abredatafile = os.path.join(self.outdir_input.text(), "converted.csv")
                preview_logger = ThrustAnalyzer(abredatafile, self.outdir_input.text(), "データ取得開始時", "推力[N]")
                auto_start = preview_logger.burn_start_time
                auto_end = preview_logger.operation_end_time
                auto_burn_end = auto_start + (preview_logger.burn_end_time * 1000000.0)
            except Exception:
                auto_start = min_x
                auto_end = max_x
                auto_burn_end = min_x + (max_x - min_x) * 0.5
            
            if not (min_x <= auto_start <= max_x) or not (min_x <= auto_end <= max_x) or auto_start >= auto_end:
                auto_start, auto_end = min_x, max_x
            if not (min_x <= auto_burn_end <= max_x):
                auto_burn_end = min_x + (max_x - min_x) * 0.5

            auto_start_sec = auto_start / 1000000.0
            auto_end_sec = auto_end / 1000000.0
            auto_burn_end_sec = auto_burn_end / 1000000.0

            self.region.setRegion([auto_start_sec, auto_end_sec])
            self.burn_line.setPos(auto_burn_end_sec)
            
            starttime = auto_start_sec
            endtime = auto_end_sec
        else:
            starttime = float(st_text)
            endtime = float(et_text)

        margin = (endtime - starttime) * 0.05
        self.plot_widget.setXRange(starttime - margin, endtime + margin, padding=0)
        
        st_us = starttime * 1000000.0
        et_us = endtime * 1000000.0
        selected_col = self.preview_col_combo.currentText()
        mask = (self.preview_df["データ取得開始時"] >= st_us) & (self.preview_df["データ取得開始時"] <= et_us)
        if mask.any():
            local_max_y = self.preview_df.loc[mask, selected_col].max()
            self.plot_widget.setYRange(0, local_max_y * 1.1, padding=0)
        self.is_zoomed_to_selection = True

    def show_burn_end_line(self):
        if not self.ensure_data_loaded():
            return
            
        st_text = self.starttime_input.text().strip()
        et_text = self.endtime_input.text().strip()
        if not st_text or not et_text:
            self.show_selected_region()
            st_text = self.starttime_input.text().strip()
            et_text = self.endtime_input.text().strip()
            
        starttime = float(st_text)
        endtime = float(et_text)
        center = starttime + (endtime - starttime) * 0.5
        
        self.burn_line.setPos(center)
        self.burn_line.show()
        self.is_burn_line_visible = True
        self.update_burn_line()

    def update_region(self):
        minX, maxX = self.region.getRegion()
        self.starttime_input.setText(f"{minX:.3f}")
        self.endtime_input.setText(f"{maxX:.3f}")

    def show_burn_line(self):
        minX, maxX = self.region.getRegion()
        center = minX + (maxX - minX) * 0.5
        self.burn_line.setPos(center)
        self.burn_line.show()
        self.is_burn_line_visible = True
        self.update_burn_line()

    def update_burn_line(self):
        pos = self.burn_line.value()
        self.burn_endtime_input.setText(f"{pos:.3f}")

    def manual_update_region(self):
        try:
            st = float(self.starttime_input.text().strip())
            et = float(self.endtime_input.text().strip())
            self.region.sigRegionChanged.disconnect(self.update_region)
            self.region.setRegion([st, et])
            self.region.sigRegionChanged.connect(self.update_region)
        except ValueError:
            pass

    def manual_update_burn_line(self):
        try:
            pos = float(self.burn_endtime_input.text().strip())
            self.burn_line.sigPositionChanged.disconnect(self.update_burn_line)
            self.burn_line.setPos(pos)
            self.burn_line.sigPositionChanged.connect(self.update_burn_line)
        except ValueError:
            pass

    def reset_preview_view(self):
        if self.preview_df is not None:
            max_y = self.preview_df[self.preview_col_combo.currentText()].max()
            min_x = self.preview_df["データ取得開始時"].min() / 1000000.0
            max_x = self.preview_df["データ取得開始時"].max() / 1000000.0
            self.plot_widget.setYRange(0, max_y * 1.1, padding=0)
            self.plot_widget.setXRange(min_x, max_x, padding=0)
        else:
            self.plot_widget.autoRange()

    def run_analysis(self):
        try:
            # GUIからの入力値を取得
            abrawfile = self.rawfile_input.text()
            if not abrawfile or not os.path.exists(abrawfile):
                QMessageBox.warning(self, "警告", "Rawデータファイルが選択されていないか、存在しません。\n再度解析を実行するには正しいRawデータファイルを選択してください。")
                return

            aboutdir = self.outdir_input.text()
            loadcell_max_lbf = int(self.loadcell_combo.currentText())
            loggertype = self.loggertype_combo.currentText()

            st_text = self.starttime_input.text().strip()
            et_text = self.endtime_input.text().strip()
            bt_text = self.burn_endtime_input.text().strip()
            # Convert GUI seconds back to microseconds for Logger
            starttime = float(st_text) * 1000000.0 if st_text else None
            endtime = float(et_text) * 1000000.0 if et_text else None
            burn_endtime = float(bt_text) * 1000000.0 if bt_text else None

            date = os.path.basename(os.path.dirname(abrawfile)) if abrawfile else "unknown_date"
            abredatafile = os.path.join(aboutdir, "converted.csv")

            os.makedirs(aboutdir, exist_ok=True)

            self.run_btn.setEnabled(False)
            self.run_btn.setText("処理中...")
            self.status_label.setText("ステータス: 解析を実行中...")
            self.status_label.setStyleSheet("font-weight: bold; color: blue; padding: 2px;")
            QApplication.processEvents() # UIの更新を反映

            # プログレスバーの初期化
            progress = QProgressDialog("処理を開始します...", "", 0, 100, self)
            progress.setWindowTitle("解析実行中")
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setCancelButton(None) # キャンセル不可
            progress.setMinimumDuration(0)
            progress.setValue(0)
            QApplication.processEvents()

            # 解析実行 (main.py と同等の処理)
            progress.setLabelText("Rawデータを変換中...")
            progress.setValue(10)
            QApplication.processEvents()
            
            RawDataConverter(abrawfile, abredatafile, loadcell_max_lbf, loggertype).convert()

            progress.setLabelText("データを分析中...")
            progress.setValue(30)
            QApplication.processEvents()
            logger = ThrustAnalyzer(abredatafile, aboutdir, "データ取得開始時", "推力[N]", starttime, endtime, burn_endtime)

            exportcsv = logger.bdf
            exportcsv = exportcsv[exportcsv["データ取得開始時"]>0]
            self.analyzed_df = exportcsv

            # CSV出力ボタンで保存するため保持しておく
            self.onlythurst_df = logger.bbdf

            total, op, avg = logger.burn_totalimpulse, logger.operating_totalimpulse, logger.average_thrust

            # 前回の古い一時ディレクトリを削除
            if self.temp_dir and os.path.exists(self.temp_dir):
                try:
                    shutil.rmtree(self.temp_dir)
                except Exception as e:
                    print(f"古い一時ディレクトリの削除に失敗: {e}")

            # 画像を一時ディレクトリに生成
            self.temp_dir = tempfile.mkdtemp()
            graph = GraphGenerator(self.temp_dir, logger.bdf, "データ取得開始時")
            progress.setLabelText("個別グラフ画像を生成中...")
            progress.setValue(50)
            QApplication.processEvents()
            
            image_paths_series = []
            image_paths_overview = []

            # データフレームに存在する列のうち、許可するものだけをdfの列の順序に従って抽出
            allowed_cols = [
                "推力[N]", "補正推力[N]", "平均推力[N]", "偏差標準偏差[N]",
                "圧力1[Pa]", "圧力2[Pa]", "圧力3[Pa]", "圧力4[Pa]",
                "低域温度1[℃]", "低域温度2[℃]", "低域温度3[℃]", 
                "高域温度1[℃]", "高域温度2[℃]",
                "温度1[℃]", "温度2[℃]", "温度3[℃]", "温度4[℃]", "温度5[℃]", "温度6[℃]"
            ]
            cols_to_plot = [col for col in logger.bdf.columns if col in allowed_cols]
            total_cols = len(cols_to_plot)
            
            for i, col in enumerate(cols_to_plot):
                safe_col = col.replace("/", "／")
                filename = f"{safe_col}.png"
                graph.generate_general_graph([col], filename)
                image_paths_series.append(os.path.join(self.temp_dir, filename))
                
                progress.setValue(50 + int(30 * (i + 1) / total_cols))
                QApplication.processEvents()

            operationendrelative = (logger.operation_end_time - logger.burn_start_time)/1000000
            
            progress.setLabelText("概要グラフ画像を生成中...")
            progress.setValue(80)
            QApplication.processEvents()

            # 概要グラフの出力 (推力 × 圧力をそれぞれ別々に作成)
            overview_thrusts = ["推力[N]", "平均推力[N]", "補正推力[N]"]
            overview_pressures = [None, "圧力1[Pa]", "圧力2[Pa]"]
            
            for t_name in overview_thrusts:
                if t_name in logger.bdf.columns:
                    for p_name in overview_pressures:
                        if p_name is None or p_name in logger.bdf.columns:
                            graph.generate_overview_graph("データ取得開始時", t_name, p_name, logger.burn_end_time, operationendrelative, logger.operating_totalimpulse, logger.burn_totalimpulse, date)
                            safe_t = t_name.replace("/", "／")
                            if p_name is not None:
                                safe_p = p_name.replace("/", "／")
                                filename = f"{safe_t}_{safe_p}.png"
                            else:
                                filename = f"{safe_t}_のみ.png"
                            image_paths_overview.append(os.path.join(self.temp_dir, filename))

            # 周波数解析ヒートマップの生成
            progress.setLabelText("周波数解析ヒートマップを生成中...")
            progress.setValue(90)
            QApplication.processEvents()

            heatmap_filename = "推力周波数解析ヒートマップ.png"
            heatmap_path = os.path.join(self.temp_dir, heatmap_filename)
            graph.generate_thrust_heatmap("推力[N]", logger.burn_end_time, heatmap_path)

            progress.setValue(100)
            QApplication.processEvents()

            # 結果データをテキストファイルに自動保存する
            result_txt_path = os.path.join(aboutdir, "analysis_results.txt")
            try:
                with open(result_txt_path, "w", encoding="utf-8") as f:
                    f.write(f"定常偏差[N]: {logger.ess}\n")
                    f.write(f"燃焼開始時間[us]: {logger.burn_start_time}\n")
                    f.write(f"作動終了時間[us]: {logger.operation_end_time}\n")
                    f.write(f"燃焼終了時間(相対秒)[s]: {logger.burn_end_time}\n")
                    f.write(f"作動時間(相対秒)[s]: {operationendrelative}\n")
                    f.write(f"燃焼時間平均推力[N]: {avg}\n")
                    f.write(f"最大推力(補正前)[N]: {logger.max_thrust_raw}\n")
                    f.write(f"最大推力(補正後)[N]: {logger.max_thrust_corrected}\n")
                    f.write(f"燃焼時間トータルインパルス[N・s]: {logger.burn_totalimpulse}\n")
                    f.write(f"作動時間トータルインパルス[N・s]: {logger.operating_totalimpulse}\n")
            except Exception as e:
                print(f"結果テキストファイルの書き込みに失敗しました: {e}")

            self.result_label.setText(
                f"【解析結果】\n"
                f"定常偏差: {round(logger.ess, 1)} N\n"
                f"燃焼時間: {round(logger.burn_end_time, 3)} s\n"
                f"作動時間: {round(operationendrelative, 3)} s\n"
                f"燃焼時間平均推力: {round(avg, 1)} N\n"
                f"最大推力 (補正前): {round(logger.max_thrust_raw, 1)} N\n"
                f"最大推力 (補正後): {round(logger.max_thrust_corrected, 1)} N\n"
                f"燃焼時間トータルインパルス: {round(logger.burn_totalimpulse, 1)} N・s\n"
                f"作動時間トータルインパルス: {round(logger.operating_totalimpulse, 1)} N・s"
            )

            # ダイアログは出さず、変数にパス情報を保存して画像表示ボタンを有効化する
            self.image_paths_dict = {
                "個別グラフ": image_paths_series,
                "概要グラフ": image_paths_overview,
                "周波数解析": [heatmap_path]
            }
            self.save_csv_btn.setEnabled(True)
            self.show_images_btn.setEnabled(True)
            
            # メッセージボックスの代わりにステータスラベルを更新
            self.status_label.setText("ステータス: 解析が終了しました。(結果を自動保存しました)")
            self.status_label.setStyleSheet("font-weight: bold; color: green; padding: 2px;")

        except Exception as e:
            self.status_label.setText("ステータス: エラーが発生しました")
            self.status_label.setStyleSheet("font-weight: bold; color: red; padding: 2px;")
            QMessageBox.critical(self, "エラー", f"処理中にエラーが発生しました:\n{str(e)}")
        finally:
            self.check_run_btn_state()
            self.run_btn.setText("解析を実行")

    def export_csv(self):
        if self.analyzed_df is None or self.onlythurst_df is None:
            QMessageBox.warning(self, "エラー", "出力するデータがありません。先に解析を実行してください。")
            return
            
        aboutdir = self.outdir_input.text()
        if not aboutdir:
            QMessageBox.warning(self, "エラー", "出力先フォルダが設定されていません。")
            return
            
        try:
            self.analyzed_df.to_csv(os.path.join(aboutdir, "burntime.csv"), index=False)
            self.onlythurst_df.to_csv(os.path.join(aboutdir, "onlythurst.csv"), index=False, header=False)
            
            abrawfile = self.rawfile_input.text()
            loggertype = self.loggertype_combo.currentText()
            if abrawfile and os.path.exists(abrawfile):
                loadcell_max_lbf = int(self.loadcell_combo.currentText())
                rc = RawDataConverter(abrawfile, os.path.join(aboutdir, "converted.csv"), loadcell_max_lbf, loggertype)
                rc.create_light()
                
            QMessageBox.information(self, "成功", f"以下のCSVファイルを出力しました:\n・LOG_light.csv\n・burntime.csv\n・onlythurst.csv\n\n出力先:\n{aboutdir}")
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"CSVファイルの出力に失敗しました:\n{e}")

    def show_images(self):
        aboutdir = self.outdir_input.text()
        if not aboutdir:
            QMessageBox.warning(self, "エラー", "出力先フォルダが設定されていません。")
            return
            
        if self.image_paths_dict:
            viewer = ImageViewerDialog(self.image_paths_dict, aboutdir, self)
            viewer.exec()
        else:
            QMessageBox.information(self, "情報", "表示できる画像がありません。")
            
    def refer_past_analysis(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "過去の解析結果ファイルを選択", "", "テキストファイル (analysis_results.txt);;すべてのファイル (*)")
        if not file_path:
            return
            
        try:
            # Parse the file
            data = {}
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if ":" in line:
                        parts = line.split(":", 1)
                        key = parts[0].strip()
                        # Normalize key by stripping units like [N]
                        norm_key = key.split("[")[0].strip()
                        # Clean values
                        val_str = parts[1].strip()
                        cleaned_val = val_str.replace("N・s", "").replace("N·s", "").replace("Ns", "")
                        cleaned_val = cleaned_val.replace("N", "").replace("s", "").replace("us", "").strip()
                        data[norm_key] = cleaned_val
            
            # Extract values
            ess = float(data.get("定常偏差", 0.0))
            burn_start_time = float(data.get("燃焼開始時間", 0.0))
            operation_end_time = float(data.get("作動終了時間", 0.0))
            burn_end_time_rel = float(data.get("燃焼終了時間(相対秒)", data.get("燃焼終了時間", 0.0)))
            operation_end_time_rel = float(data.get("作動時間(相対秒)", data.get("作動時間", 0.0)))
            avg_thrust = float(data.get("燃焼時間平均推力", 0.0))
            max_thrust_raw = float(data.get("最大推力(補正前)", data.get("最大推力", 0.0)))
            max_thrust_corrected = float(data.get("最大推力(補正後)", 0.0))
            burn_totalimpulse = float(data.get("燃焼時間トータルインパルス", 0.0))
            operating_totalimpulse = float(data.get("作動時間トータルインパルス", 0.0))
            
            # Load converted.csv if exists in the same directory
            dir_path = os.path.dirname(file_path)
            converted_path = os.path.join(dir_path, "converted.csv")
            if os.path.exists(converted_path):
                self.status_label.setText("ステータス: 過去のデータを読み込み中...")
                self.status_label.setStyleSheet("font-weight: bold; color: blue; padding: 2px;")
                QApplication.processEvents()
                
                self.preview_df = pandas.read_csv(converted_path)
                
                # GUIの状態変数と同期させて ensure_data_loaded() による意図しない再変換・上書きを防止
                self.current_rawfile = self.rawfile_input.text()
                self.current_loadcell = int(self.loadcell_combo.currentText())
                self.current_loggertype = self.loggertype_combo.currentText()
                
                self.outdir_input.setText(dir_path) # Set the output dir to the loaded folder
                
                # Replot graph
                self.replot_graph()
                
                # Set slider boundaries without triggering infinite loops
                self.region.sigRegionChanged.disconnect(self.update_region)
                self.region.setRegion([burn_start_time / 1000000.0, operation_end_time / 1000000.0])
                self.region.sigRegionChanged.connect(self.update_region)
                
                self.burn_line.sigPositionChanged.disconnect(self.update_burn_line)
                self.burn_line.setPos((burn_start_time / 1000000.0) + burn_end_time_rel)
                self.burn_line.sigPositionChanged.connect(self.update_burn_line)
                
                self.burn_line.show()
                self.is_burn_line_visible = True
                
                # Update text boxes manually
                self.starttime_input.setText(f"{burn_start_time / 1000000.0:.3f}")
                self.endtime_input.setText(f"{operation_end_time / 1000000.0:.3f}")
                self.burn_endtime_input.setText(f"{((burn_start_time / 1000000.0) + burn_end_time_rel):.3f}")
                
                # Zoom to region
                self.show_selected_region()
                
                self.status_label.setText("ステータス: 過去の解析を参照中")
                self.status_label.setStyleSheet("font-weight: bold; color: green; padding: 2px;")
            else:
                QMessageBox.warning(self, "警告", "同じフォルダ内に converted.csv が見つからないため、グラフは描画されません。数値のみ更新します。")
                self.status_label.setText("ステータス: 数値データのみ読込完了")
                self.status_label.setStyleSheet("font-weight: bold; color: orange; padding: 2px;")

            # Display values in the label
            self.result_label.setText(
                f"【解析結果】\n"
                f"定常偏差: {round(ess, 1)} N\n"
                f"燃焼時間: {round(burn_end_time_rel, 3)} s\n"
                f"作動時間: {round(operation_end_time_rel, 3)} s\n"
                f"燃焼時間平均推力: {round(avg_thrust, 1)} N\n"
                f"最大推力 (補正前): {round(max_thrust_raw, 1)} N\n"
                f"最大推力 (補正後): {round(max_thrust_corrected, 1)} N\n"
                f"燃焼時間トータルインパルス: {round(burn_totalimpulse, 1)} N・s\n"
                f"作動時間トータルインパルス: {round(operating_totalimpulse, 1)} N・s"
            )
            
            self.save_csv_btn.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"過去の解析データの読み込みに失敗しました:\n{e}")

    def closeEvent(self, event):
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                print(f"終了時の一時ディレクトリ削除に失敗: {e}")
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = ThrustAnalyzerGUI()
    gui.show()
    sys.exit(app.exec())