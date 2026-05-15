import pandas as pd
import os

class Logger:
    def __init__(self,data_file,out_dir,time_name,thrust_name):
        self.filepath=data_file
        self.out_dir=out_dir
        self.time_name=time_name
        self.thrust_name=thrust_name
        #private
        self.df=pd.read_csv(self.filepath,header=0)
        self.bdf=None #burn data frame
        self.bbdf=None #burn data frame

        #実験値
        self.loadcell_max_lbf=1000

        #public
        self.calcu_moving_ave("推力[N]","平均推力[N]")
        self.calcu_moving_ave("圧力1[Pa]","平均圧力1[Pa]")
        self.calcu_moving_ave("圧力2[Pa]","平均圧力2[Pa]")
        self.calcu_moving_ave("圧力3[Pa]","平均圧力3[Pa]")
        self.calcu_moving_ave("圧力4[Pa]","平均圧力4[Pa]")
        
        self.burn_start_time= self.calcu_burn_start_time("平均推力[N]") #燃焼開始時間
        self.ess=self.calcu_thrust_ess() #定常偏差
        self.correct_thurst("補正推力[N]") #補正推力の計算
        self.operation_end_time=self.calcu_operation_end_time("補正推力[N]") #作動時間終了時間
        self.create_burndata() #燃焼データの作成
        self.burn_end_time=self.calcu_burn_end_time("平均推力[N]") #燃焼終了時間
        
        self.burn_totalimpulse,self.operating_totalimpulse,self.average_thrust=self.calcu_totalimpulse("補正推力[N]") #燃焼トータルインパルス
        #マジックナンバー
        self.threshold_offset=20

    def calcu_moving_ave(self,before_series,after_series):
        self.df[after_series] = self.df[before_series].rolling(window=100,min_periods=1).mean()

    def calcu_thrust_ess(self):
        if self.burn_start_time is None:
            raise ValueError("燃焼開始時間が設定されていません。先にcalcu_burn_start_time()を実行してください。")
        ess = self.df[self.df[self.time_name]<self.burn_start_time][self.thrust_name].median()
        return ess

    def create_burndata(self):
        print("燃焼開始時(micros)",self.burn_start_time)
        print("燃焼終了時(micros)",self.operation_end_time)
        self.bdf=self.df[(self.df[self.time_name]>self.burn_start_time-500000)&(self.df[self.time_name]<self.operation_end_time+500000)].copy()
        self.bbdf=self.df[(self.df[self.time_name]>=self.burn_start_time+3140000)&(self.df[self.time_name]<=self.operation_end_time)][[self.time_name,self.thrust_name]].copy()

        #時間調整
        self.bdf[self.time_name] = (self.bdf[self.time_name] - self.burn_start_time) /1000000
        self.bbdf[self.time_name] = (self.bbdf[self.time_name] - self.burn_start_time-3140000) /1000000

    
    def correct_thurst(self,after_thurst_name):
        self.df[after_thurst_name] = self.df[self.thrust_name] - self.ess

    def calcu_burn_start_time(self, average_thrust_series_name):
        series = self.df[average_thrust_series_name]
        diff = series.diff() > 1
        groups = diff.groupby((diff != diff.shift()).cumsum())
        burn_start_time=0
        for name, group in groups:
            if group.iloc[0] and len(group) >= 10:
                start_idx = group.index[0]
                burn_start_time = self.df.loc[start_idx, self.time_name]
                break
        if burn_start_time is None:
            burn_start_time = 0
        return burn_start_time

    def calcu_burn_end_time(self,average_thrust_name):
        self.bdf["偏差[N]"] = self.bdf[self.thrust_name] - self.bdf[average_thrust_name]
        self.bdf["偏差標準偏差[N]"] = self.bdf["偏差[N]"].rolling(window=100,min_periods=1).std()
        burn_end_time = self.bdf[(self.bdf["偏差標準偏差[N]"] >10)].iloc[-1][self.time_name]
        return burn_end_time
    
    def calcu_operation_end_time(self,correct_thurst_name):
        mask = self.df[correct_thurst_name] > self.df[correct_thurst_name].max() * 0.05
        print("maxthurst", self.df[correct_thurst_name].max(),"N")
        operation_end_time = self.df[mask].iloc[-1][self.time_name]
        return operation_end_time
    def calcu_totalimpulse(self,correct_thurst_name):
        burn_totalimpulse = self.bdf[self.bdf[self.time_name] < self.burn_end_time][correct_thurst_name].sum() * 0.001
        mask = self.bdf[correct_thurst_name] > self.bdf[correct_thurst_name].max() * 0.05
        operating_totalimpulse = self.bdf[mask][correct_thurst_name].sum() * 0.001
        average_thrust = burn_totalimpulse / (self.burn_end_time)
        return burn_totalimpulse,operating_totalimpulse,average_thrust

    

if __name__ == "__main__":
    datafile="2025-12-06-01/converted.csv"
    outdir="codetest/out2"
    logger_instance=Logger(datafile,outdir)
    logger_instance.fast_analysis()