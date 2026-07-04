import pandas as pd

class ThrustAnalyzer:
    def __init__(self, data_file, out_dir, time_name, thrust_name, starttime=None, endtime=None, burn_endtime=None):
        self.filepath = data_file
        self.out_dir = out_dir
        self.time_name = time_name
        self.thrust_name = thrust_name
        # private
        self.df = pd.read_csv(self.filepath, header=0)
        self.bdf = None  # 燃焼前後のバッファを含むDataFrame
        self.bbdf = None # 厳密な作動区間のみのDataFrame

        # 各チャンネルの移動平均を算出
        self.calcu_moving_ave("推力[N]", "平均推力[N]")
        self.calcu_moving_ave("圧力1[Pa]", "平均圧力1[Pa]")
        self.calcu_moving_ave("圧力2[Pa]", "平均圧力2[Pa]")
        self.calcu_moving_ave("圧力3[Pa]", "平均圧力3[Pa]")
        self.calcu_moving_ave("圧力4[Pa]", "平均圧力4[Pa]")
        
        # 燃焼開始時間の決定
        self.burn_start_time = starttime if starttime is not None else self.calcu_burn_start_time("平均推力[N]")

        # 定常偏差の決定と補正
        self.ess = self.calcu_thrust_ess()
        self.correct_thurst("補正推力[N]")

        # 作動終了時間の決定とデータ区間の作成
        self.operation_end_time = endtime if endtime is not None else self.calcu_operation_end_time("補正推力[N]")
        self.create_burndata()

        # グラフ描画用の中間列（偏差等）の生成
        self.bdf["偏差[N]"] = self.bdf[self.thrust_name] - self.bdf["平均推力[N]"]
        self.bdf["偏差標準偏差[N]"] = self.bdf["偏差[N]"].rolling(window=100, min_periods=1).std()

        # 燃焼終了時間の決定
        self.burn_end_time = (burn_endtime - self.burn_start_time) / 1000000.0 if burn_endtime is not None else self.calcu_burn_end_time("平均推力[N]")
        
        # トータルインパルス（燃焼・作動）および平均推力の算出
        self.burn_totalimpulse, self.operating_totalimpulse, self.average_thrust = self.calcu_totalimpulse("補正推力[N]")

        # 最大推力（補正前・補正後）の算出
        active_df = self.df[(self.df[self.time_name] >= self.burn_start_time) & (self.df[self.time_name] <= self.operation_end_time)]
        if not active_df.empty:
            self.max_thrust_raw = active_df[self.thrust_name].max()
            self.max_thrust_corrected = active_df["補正推力[N]"].max()
        else:
            self.max_thrust_raw = 0.0
            self.max_thrust_corrected = 0.0

    def calcu_moving_ave(self, before_series, after_series):
        self.df[after_series] = self.df[before_series].rolling(window=100, min_periods=1).mean()

    def calcu_thrust_ess(self):
        if self.burn_start_time is None:
            raise ValueError("燃焼開始時間が設定されていません。")
        ess_df = self.df[self.df[self.time_name] < self.burn_start_time]
        if ess_df.empty:
            return 0.0
        ess = ess_df[self.thrust_name].median()
        return 0.0 if pd.isna(ess) else ess

    def create_burndata(self, correct_thurst_name="補正推力[N]"):
        # グラフ表示用に前後0.5秒(500,000us)のバッファを持たせた範囲を切り出す
        self.bdf = self.df[(self.df[self.time_name] > self.burn_start_time - 500000) & (self.df[self.time_name] < self.operation_end_time + 500000)].copy()
        # 厳密な積分およびCSV出力用の区間
        self.bbdf = self.df[(self.df[self.time_name] >= self.burn_start_time-1) & (self.df[self.time_name] <= self.operation_end_time)][[self.time_name, correct_thurst_name]].copy()

        # 時間軸の調整（燃焼開始時刻を0秒とした相対秒へ変換）
        self.bdf[self.time_name] = (self.bdf[self.time_name] - self.burn_start_time) / 1000000.0
        self.bbdf[self.time_name] = (self.bbdf[self.time_name] - self.burn_start_time) / 1000000.0
    
    def correct_thurst(self, after_thurst_name):
        self.df[after_thurst_name] = self.df[self.thrust_name] - self.ess

    def calcu_burn_start_time(self, average_thrust_series_name):
        series = self.df[average_thrust_series_name]
        diff = series.diff() > 1
        groups = diff.groupby((diff != diff.shift()).cumsum())
        for name, group in groups:
            if group.iloc[0] and len(group) >= 10:
                return self.df.loc[group.index[0], self.time_name]
        return self.df[self.time_name].iloc[0]

    def calcu_burn_end_time(self, average_thrust_name):
        self.bdf["偏差[N]"] = self.bdf[self.thrust_name] - self.bdf[average_thrust_name]
        self.bdf["偏差標準偏差[N]"] = self.bdf["偏差[N]"].rolling(window=100, min_periods=1).std()
        
        mask = self.bdf["偏差標準偏差[N]"] > 10
        if not self.bdf[mask].empty:
            return self.bdf[mask].iloc[-1][self.time_name]
        return self.bdf[self.time_name].max()
    
    def calcu_operation_end_time(self, correct_thurst_name):
        mask = self.df[correct_thurst_name] > self.df[correct_thurst_name].max() * 0.05
        if not self.df[mask].empty:
            return self.df[mask].iloc[-1][self.time_name]
        return self.df[self.time_name].iloc[-1]

    def calcu_totalimpulse(self, correct_thurst_name):
        # 各行の時間差分を秒単位で計算して高精度に数値積分
        dt_bdf = self.bdf[self.time_name].diff().bfill().fillna(0.001)
        
        # 燃焼トータルインパルスの計算 (相対時間0から燃焼終了まで)
        burn_mask = (self.bdf[self.time_name] >= 0) & (self.bdf[self.time_name] < self.burn_end_time)
        burn_totalimpulse = (self.bdf.loc[burn_mask, correct_thurst_name] * dt_bdf[burn_mask]).sum()
        
        # 作動トータルインパルスの計算 (作動区間 bbdf 全体の積分)
        dt_bbdf = self.bbdf[self.time_name].diff().bfill().fillna(0.001)
        operating_totalimpulse = (self.bbdf[correct_thurst_name] * dt_bbdf).sum()
        
        average_thrust = burn_totalimpulse / self.burn_end_time if self.burn_end_time > 0 else 0
        return burn_totalimpulse, operating_totalimpulse, average_thrust
