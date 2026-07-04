import polars as pl
import os

class RawDataConverter:
    def __init__(self, rawfile, outputfile, loadcell_max_lbf, loggertype):
        self.rawfile = rawfile
        self.outputfile = outputfile
        self.loadcell_max_lbf = loadcell_max_lbf
        self.loggertype = loggertype
        # --- 定数定義 ---
        self.VOLTAGE_REF_5V = 4.99

        self.R0 = 10000
        self.T0 = 25 + 273.15
        self.Tempnew_B = 4126
        self.Temp_B = 3435

        self.HighTemp_R = 10000
        self.LowTemp_R = 1000

    # --- 計算ロジック（エクスプレッションを返す関数） ---
    def adc_voltage(self, col_name):
        """バイナリ値を電圧に変換する計算式"""
        return (self.VOLTAGE_REF_5V * pl.col(col_name)) / 4095.0

    def thrust(self, col_name, max_lbf):
        """推力の計算式を返す"""
        if max_lbf == 250:
            return 0.5807 * pl.col(col_name) - 24.098
        elif max_lbf == 500:
            return 1.2836 * pl.col(col_name) - 49.93
        else: # 1000
            return 2.3896 * pl.col(col_name) - 115.47

    def pressure(self, col_name):
        """圧力の計算式を返す"""
        v = self.adc_voltage(col_name)
        return 2.0 * v * 1e6

    def temp(self, col_name, R, B):
        """サーミスタ温度の計算式を返す"""
        v = self.adc_voltage(col_name)
        # ゼロ除算回避
        v_safe = pl.when(v >= self.VOLTAGE_REF_5V).then(self.VOLTAGE_REF_5V - 1e-6).otherwise(v)

        rt = R * v_safe / (self.VOLTAGE_REF_5V - v_safe)
        t_kelvin = 1 / ((1 / B) * (rt / self.R0).log() + (1 / self.T0))
        return t_kelvin - 273.15

    def temp_new(self, col_name):
        """新ロガー用のサーミスタ温度の計算式（Polars Expression）を返す"""
        adc_val = pl.col(col_name)
        # r1 = 10000.0 * adc_val / 4095.0
        r1 = 10000.0 * adc_val / 4095.0
        
        # log エラー・ゼロ・負数回避ガード
        r1_safe = pl.when(r1 <= 1e-6).then(1e-6).otherwise(r1)
        
        R = 200000.0
        B = 3500.0
        T0 = 25.0 + 273.15
        
        t_kelvin = B / ((r1_safe / R).log() + B / T0)
        return t_kelvin - 273.15

    # --- メイン処理 ---
    def convert(self):
        if self.loggertype == "new":
            self.convert_new()
        elif self.loggertype == "old":
            self.convert_old()

    def create_light(self):
        out_dir = os.path.dirname(self.outputfile)
        light_rawfile = os.path.join(out_dir, "LOG_light.csv")
        has_hdr = (self.loggertype == "new")
        df = pl.read_csv(self.rawfile, has_header=has_hdr, ignore_errors=True)
        df_light = df.gather_every(100)
        df_light.write_csv(light_rawfile, include_bom=True)
    
    def convert_old(self):
        col_names = [f"column_{i}" for i in range(20)]
        df = pl.read_csv(self.rawfile, has_header=False, new_columns=col_names)

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

        df_result.write_csv(self.outputfile, include_bom=True)

    def convert_new(self):
        col_names = [f"column_{i}" for i in range(18)]
        df = pl.read_csv(self.rawfile, has_header=True, new_columns=col_names)

        df_result = df.select([
            pl.col("column_0").alias("データ取得開始時"),
            pl.col("column_1").alias("データ取得終了時"),
            self.thrust("column_2", self.loadcell_max_lbf).alias("推力[N]"),
            self.pressure("column_4").alias("圧力1[Pa]"),
            self.pressure("column_5").alias("圧力2[Pa]"),
            self.pressure("column_6").alias("圧力3[Pa]"),
            self.pressure("column_7").alias("圧力4[Pa]"),
            self.temp_new("column_10").alias("温度1[℃]"),
            self.temp_new("column_11").alias("温度2[℃]"),
            self.temp_new("column_12").alias("温度3[℃]"),
            self.temp_new("column_13").alias("温度4[℃]"),
            self.temp_new("column_14").alias("温度5[℃]"),
            self.temp_new("column_15").alias("温度6[℃]")
        ])

        df_result.write_csv(self.outputfile, include_bom=True)
