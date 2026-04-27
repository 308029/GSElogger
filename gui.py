import sys
import os
import time
import pandas
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QFormLayout, QLineEdit, QPushButton, QComboBox,
                             QFileDialog, QMessageBox)

# 既存の解析モジュールをインポート
from analysis import RawConverter
from dataanlysis import Logger
from graphgenerator import graph_generator

class LoggerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('ロガー結果 解析GUI')
        self.resize(550, 400)

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Raw File
        self.rawfile_input = QLineEdit()
        self.rawfile_btn = QPushButton("参照")
        self.rawfile_btn.clicked.connect(self.browse_rawfile)
        rawfile_layout = QHBoxLayout()
        rawfile_layout.addWidget(self.rawfile_input)
        rawfile_layout.addWidget(self.rawfile_btn)
        form_layout.addRow("Rawデータファイル (CSV):", rawfile_layout)

        # Output Directory
        self.outdir_input = QLineEdit()
        self.outdir_btn = QPushButton("参照")
        self.outdir_btn.clicked.connect(self.browse_outdir)
        outdir_layout = QHBoxLayout()
        outdir_layout.addWidget(self.outdir_input)
        outdir_layout.addWidget(self.outdir_btn)
        form_layout.addRow("出力先フォルダ:", outdir_layout)

        # Mode
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["manual", "full"])
        form_layout.addRow("モード (mode):", self.mode_combo)

        # Loadcell Max LBF
        self.loadcell_combo = QComboBox()
        self.loadcell_combo.addItems(["500", "250", "1000"])
        form_layout.addRow("ロードセル最大推力 (loadcell_max_lbf):", self.loadcell_combo)

        # Logger Type
        self.loggertype_combo = QComboBox()
        self.loggertype_combo.addItems(["new", "old"])
        form_layout.addRow("ロガータイプ (loggertype):", self.loggertype_combo)

        # Start Time (Manual mode settings)
        self.starttime_input = QLineEdit()
        self.starttime_input.setPlaceholderText("指定しない場合は空欄 (None)")
        form_layout.addRow("開始時間 (starttime):", self.starttime_input)

        # End Time (Manual mode settings)
        self.endtime_input = QLineEdit()
        self.endtime_input.setPlaceholderText("指定しない場合は空欄 (None)")
        form_layout.addRow("終了時間 (endtime):", self.endtime_input)

        layout.addLayout(form_layout)

        # Run Button
        self.run_btn = QPushButton("解析を実行")
        self.run_btn.setStyleSheet("font-weight: bold; padding: 10px;")
        self.run_btn.clicked.connect(self.run_analysis)
        layout.addWidget(self.run_btn)

        self.setLayout(layout)

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

    def run_analysis(self):
        try:
            # GUIからの入力値を取得
            abrawfile = self.rawfile_input.text()
            aboutdir = self.outdir_input.text()
            mode = self.mode_combo.currentText()
            loadcell_max_lbf = int(self.loadcell_combo.currentText())
            loggertype = self.loggertype_combo.currentText()

            st_text = self.starttime_input.text().strip()
            et_text = self.endtime_input.text().strip()
            starttime = float(st_text) if st_text else None
            endtime = float(et_text) if et_text else None

            date = os.path.basename(os.path.dirname(abrawfile)) if abrawfile else "unknown_date"
            abredatafile = os.path.join(aboutdir, "converted.csv")

            os.makedirs(aboutdir, exist_ok=True)

            self.run_btn.setEnabled(False)
            self.run_btn.setText("処理中...")
            QApplication.processEvents() # UIの更新を反映

            # 解析実行 (main.py と同等の処理)
            print("Analysing raw data...")
            start = time.time()
            RawConverter(abrawfile, abredatafile, loadcell_max_lbf, loggertype).convert()
            rawconvert_time = time.time() - start

            if mode == "full":
                logger = Logger(abredatafile, aboutdir, "データ取得開始時", "推力[N]")

                start = time.time()
                print("Analysing converted data...")
                analyzing_time = time.time() - start

                exportcsv = logger.bdf
                exportcsv = exportcsv[exportcsv["データ取得開始時"]>0]
                exportcsv.to_csv(os.path.join(aboutdir,"burntime3.csv"))

                total,op,avg = logger.calcu_totalimpulse("補正推力[N]")

                graph = graph_generator(aboutdir, logger.bdf, "データ取得開始時")
                print("Creating graphs...")
                start = time.time()
                graph.generate_graph_from_series(logger.df["データ取得開始時"][::1000],logger.df["推力[N]"][::1000],"全体推力[N]")
                graph.generate_general_graph(["推力[N]","補正推力[N]","平均推力[N]","偏差標準偏差[N]"],"推力関連.png")
                graph.generate_general_graph(["圧力1[Pa]","圧力2[Pa]","圧力3[Pa]","圧力4[Pa]"],"圧力.png")
                graph.generate_general_graph(["低域温度1[℃]","低域温度2[℃]","低域温度3[℃]","高域温度1[℃]","高域温度2[℃]"],"温度.png")
                generate_graph_time = time.time() - start

                operationendrelative = (logger.operation_end_time - logger.burn_start_time)/1000000
                graph.generate_overview_graph("データ取得開始時","推力[N]",["圧力1[Pa]"],logger.burn_end_time,operationendrelative,logger.operating_totalimpulse, logger.burn_totalimpulse,date)
                graph.generate_overview_graph("データ取得開始時","平均推力[N]",["平均圧力1[Pa]"],logger.burn_end_time,operationendrelative,logger.operating_totalimpulse,logger.burn_totalimpulse,date)
                graph.generate_overview_graph("データ取得開始時","補正推力[N]",None,logger.burn_end_time,operationendrelative,logger.operating_totalimpulse,logger.burn_totalimpulse,date)

                result_msg = f"定常偏差: {round(logger.ess,1)} N\n"
                result_msg += f"燃焼終了時間: {logger.burn_end_time} s\n"
                result_msg += f"作動終了時間: {operationendrelative} s\n"
                result_msg += f"トータルインパルス: {round(total,1)} N・s\n"
                result_msg += f"作動時間トータルインパルス: {round(op,1)} N・s\n\n"
                result_msg += f"raw解析時間: {round(rawconvert_time, 2)}s\n"
                result_msg += f"データ分析時間: {round(analyzing_time, 2)}s\n"
                result_msg += f"グラフ生成時間: {round(generate_graph_time, 2)}s"

                QMessageBox.information(self, "成功", f"Fullモードの変換とグラフ生成が完了しました。\n\n{result_msg}")
            
            elif mode == "manual":
                print("Manual mode generationg graph...")
                ccsv = pandas.read_csv(abredatafile)
                if(starttime is not None):
                    ccsv=ccsv[(ccsv["データ取得開始時"]>=starttime)]
                if(endtime is not None):
                    ccsv=ccsv[(ccsv["データ取得開始時"]<=endtime)]
                
                graph = graph_generator(aboutdir, ccsv, "データ取得開始時")
                simple_list= ["推力[N]","圧力1[Pa]","圧力2[Pa]","圧力3[Pa]","圧力4[Pa]","低域温度1[℃]","低域温度2[℃]","低域温度3[℃]","高域温度1[℃]","高域温度2[℃]"]
                for colname in simple_list:
                    graph.generate_general_graph([colname], colname + ".png")

                QMessageBox.information(self, "成功", "Manualモードの変換とグラフ生成が完了しました。")

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"処理中にエラーが発生しました:\n{str(e)}")
        finally:
            self.run_btn.setEnabled(True)
            self.run_btn.setText("解析を実行")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = LoggerGUI()
    gui.show()
    sys.exit(app.exec())