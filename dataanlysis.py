import pandas as pd
import matplotlib.pyplot as plt
import japanize_matplotlib
import os

class logger:
    def __init__(self,data_file,out_dir):
        self.filepath=data_file
        self.out_dir=out_dir
        self.df=pd.read_csv(self.filepath,header=0)
        self.bdf=None #burn data frame

        #実験値
        self.loadcell_max_lbf=1000

        self.ess=None #定常偏差
        self.burn_start_time=None #燃焼開始時間
        self.burn_end_time=None #燃焼終了時間
        self.burn_totalimpulse=None #燃焼トータルインパルス
        self.operating_totalimpulse=None #作動時間トータルインパルス
        self.op_last_time=None #作動時間トータルインパルスに寄与した最後のインデックス（データ取得開始時）
        self.average_thrust=None #燃焼時間平均推力

        #マジックナンバー
        self.threshold_offset=20

    def calcu_moving_ave(self,seriesname):
        return  self.df[seriesname].rolling(window=100,min_periods=1).mean()
    
    def calcu_ess(self):
        mmedian = self.df["推力[N]"].median()
        self.ess = mmedian
        return mmedian
    
    def create_burndata(self):
        self.bdf=self.df[(self.df["データ取得開始時"]>self.burn_start_time-1000000)&(self.df["データ取得開始時"]<self.burn_start_time+8000000)&(self.df["推力[N]"]>self.ess+10)].copy()
        #時間調整
        self.bdf["データ取得開始時"] = (self.bdf["データ取得開始時"] - self.burn_start_time) /1000000
    
    def calcu_burn_start_time(self):
        mmedian = self.ess
        self.burn_start_time = self.df[self.df["推力[N]"] > mmedian+self.threshold_offset].iloc[0]["データ取得開始時"]
        return self.burn_start_time
    
    def calcu_burn_end_time(self):
        self.bdf["偏差[N]"] = self.bdf["推力[N]"] - self.bdf["平均推力[N]"]
        self.bdf["偏差標準偏差[N]"] = self.bdf["偏差[N]"].rolling(window=100,min_periods=1).std()
        self.burn_end_time = self.bdf[(self.bdf["偏差標準偏差[N]"] <50) & (self.bdf["データ取得開始時"]>3)].iloc[0]["データ取得開始時"]
        return self.burn_end_time
    
    def correct_thurst(self,seriesname):
        self.bdf["補正推力[N]"] = self.bdf[seriesname] - self.ess
    
    def calcu_totalimpulse(self):
        self.burn_totalimpulse = self.bdf[self.bdf["データ取得開始時"] < self.burn_end_time]["補正推力[N]"].sum() * 0.001
        mask = self.bdf["補正推力[N]"] > self.bdf["補正推力[N]"].max() * 0.05
        self.operating_totalimpulse = self.bdf[mask]["補正推力[N]"].sum() * 0.001
        self.op_last_time = self.bdf[mask].iloc[-1]["データ取得開始時"]
        self.average_thrust = self.burn_totalimpulse / (self.burn_end_time)
        return self.burn_totalimpulse,self.operating_totalimpulse

    def analysis_all(self):
        self.df["平均推力[N]"] = self.calcu_moving_ave("推力[N]")
        self.burn_start_time = self.calcu_burn_start_time(self.df)
        self.ess = self.calcu_ess()
        self.burn_end_time = self.calcu_burn_end_time()
        burntotalimpulse,operationgtotalimpulse = self.calcu_totalimpulse()
        self.create_thrust_graph()
        self.create_overview_graph()
        for colname in ml:
            self.create_general_graph()
        
    def fast_analysis(self):
        self.df["平均推力[N]"] = self.calcu_moving_ave("推力[N]")
        self.calcu_ess()
        self.calcu_burn_start_time()
        self.create_burndata()
        self.calcu_burn_end_time()
        self.correct_thurst("推力[N]")
        self.calcu_totalimpulse()
        
        print("作動時間トータルインパルス:", self.operating_totalimpulse)
        print("燃焼トータルインパルス:", self.burn_totalimpulse)


if __name__ == "__main__":
    datafile="2025-12-06-01/converted.csv"
    outdir="codetest/out2"
    logger_instance=logger(datafile,outdir)
    logger_instance.fast_analysis()