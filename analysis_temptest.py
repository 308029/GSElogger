import polars as pl
import numpy as np
import time

class RawConverter:
    def __init__(self, rawfile, outputfile):
        self.rawfile = rawfile
        self.outputfile = outputfile
        self.VOLTAGE_REF_5V = 4.99
        self.AMP_GAIN = 47.0

        "定数"
        self.R0 = 10000
        self.T0 = 25 + 273.15

        self.Tempnew_B = 4126
        self.Temp_B = 3435
        self.HighTemp_R = 10000
        self.LowTemp_R = 1000#?100

    def adc_voltage(self,col_name):
        return (self.VOLTAGE_REF_5V * pl.col(col_name)) / 4095.0

    def thrust(self,col_name, max_lbf):
        if max_lbf == 250:
            return 0.5807 * pl.col(col_name) - 24.098
        elif max_lbf == 500:
            return 1.2836 * pl.col(col_name) - 49.93
        else: # 1000
            return 2.3896 * pl.col(col_name) - 115.47

    def pressure(self,col_name):
        v = self.adc_voltage(col_name)
        return 2.0 * v * 1e6

    def temp(self,col_name, R, B):
        v = self.adc_voltage(col_name)
        # ゼロ除算回避（vがVOLTAGE_REF_5Vに近い場合）
        v_safe = pl.when(v >= self.VOLTAGE_REF_5V).then(self.VOLTAGE_REF_5V - 1e-6).otherwise(v)
        

        rt = R * v_safe / (self.VOLTAGE_REF_5V - v_safe)
        # サーミスタ計算式
        # T = 1 / (1/B * ln(Rt/R0) + 1/T0) - 273.15
        t_kelvin = 1 / ((1 / B) * (rt / self.R0).log() + (1 / self.T0))
        return t_kelvin - 273.15

    def convert(self):
        if self.loggertype == "new":
            self.convertnew()
        elif self.loggertype == "old":
            self.convertold()
    
    def convertold(self):
        # 1. 読み込み（必要な列だけインデックスで指定）
        # 元のコードの row[0], row[1], ... に対応
        col_names = [f"column_{i}" for i in range(20)] # 一旦仮名
        
        # scan_csvを使うと「遅延評価」になり、さらに最適化されます
        df = pl.read_csv(self.rawfile, has_header=False, new_columns=col_names)

        # 2. 変換処理（ここですべての計算を一気に定義）
        # Polarsはこれを解析してマルチスレッドで並列実行します
        df_result = df.select([
            pl.col("column_0").alias("書き込み待ちデータ数"),
            pl.col("column_1").alias("データ取得開始時"),
            pl.col("column_2").alias("データ取得終了時"),
            self.thrust("column_3", self.loadcell_max_lbf).alias("推力[N]"),
            self.pressure("column_5").alias("圧力1[Pa]"),
            self.pressure("column_6").alias("圧力2[Pa]"),
            self.pressure("column_7").alias("圧力3[Pa]"),
            self.pressure("column_8").alias("圧力4[Pa]"),
            self.temp("column_11", self.LowTemp_R, self.Temp_B).alias("低域温度1[℃]"),
            self.temp("column_12", self.LowTemp_R, self.Temp_B).alias("低域温度2[℃]"),
            self.temp("column_13", self.LowTemp_R, self.Tempnew_B).alias("低域温度3[℃]"),
            self.temp("column_14", self.HighTemp_R, self.Temp_B).alias("高域温度1[℃]"),
            self.temp("column_15", self.HighTemp_R, self.Temp_B).alias("高域温度2[℃]"),
            pl.col("column_19").alias("バルブ")
        ])

        # 3. 書き出し
        df_result.write_csv(self.outputfile, include_bom=True)

    def convertnew(self):
        # 1. 読み込み（必要な列だけインデックスで指定）
        col_names = [f"column_{i}" for i in range(18)] # 一旦仮名
        
        # scan_csvを使うと「遅延評価」になり、さらに最適化されます
        df = pl.read_csv(self.rawfile, has_header=True, new_columns=col_names)

        # 2. 変換処理（ここですべての計算を一気に定義）
        # Polarsはこれを解析してマルチスレッドで並列実行します
        df_result = df.select([
            pl.col("column_0").alias("データ取得開始時"),
            pl.col("column_1").alias("データ取得終了時"),
            self.thrust("column_2", self.loadcell_max_lbf).alias("推力[N]"),
            self.pressure("column_4").alias("圧力1[Pa]"),
            self.pressure("column_5").alias("圧力2[Pa]"),
            self.pressure("column_6").alias("圧力3[Pa]"),
            self.pressure("column_7").alias("圧力4[Pa]"),
            self.temp("column_10", self.LowTemp_R, self.Temp_B).alias("低域温度1[℃]"),
            self.temp("column_11", self.LowTemp_R, self.Temp_B).alias("低域温度2[℃]"),
            self.temp("column_12", self.LowTemp_R, self.Tempnew_B).alias("低域温度3[℃]"),
            self.temp("column_13", self.HighTemp_R, self.Temp_B).alias("高域温度1[℃]"),
            self.temp("column_14", self.HighTemp_R, self.Temp_B).alias("高域温度2[℃]")
        ])

        # 3. 書き出し
        df_result.write_csv(self.outputfile, include_bom=True)

if __name__ == "__main__":
    inputfilepath = "2025-12-06-01/LOG-0000001.csv"
    outputfilepath = "2025-12-06-01/converted.csv"
    
    start = time.time()
    raw2data = RawConverter(inputfilepath, outputfilepath)
    raw2data.convert()
    end = time.time()
    print("処理時間 (秒):", (end- start))