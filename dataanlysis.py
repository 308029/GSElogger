import pandas as pd
import os

class Logger:
    def __init__(self,data_file,out_dir):
        self.filepath=data_file
        self.out_dir=out_dir
        #private
        self.df=pd.read_csv(self.filepath,header=0)
        self.bdf=None #burn data frame
        self.df5=None

        #実験値
        self.loadcell_max_lbf=1000

        #public
        self.ess=None #定常偏差
        self.burn_start_time=None #燃焼開始時間
        self.burn_end_time=None #燃焼終了時間
        self.operation_end_time=None #作動時間終了時間
        self.burn_totalimpulse=None #燃焼トータルインパルス
        self.operating_totalimpulse=None #作動時間トータルインパルス
        self.average_thrust=None #燃焼時間平均推力

        #マジックナンバー
        self.threshold_offset=20

    def calcu_moving_ave(self,before_series,after_series):
        self.df[after_series] = self.df[before_series].rolling(window=100,min_periods=1).mean()

    def calcu_thrust_ess(self,timename,thurst_name):
        if self.burn_start_time is None:
            raise ValueError("燃焼開始時間が設定されていません。先にcalcu_burn_start_time()を実行してください。")
        self.ess = self.df[self.df[timename]<self.burn_start_time][thurst_name].median()
        return self.ess
    
    def create_burndata(self,timename,thurstname):
        print(self.burn_start_time,self.operation_end_time)
        self.bdf=self.df[(self.df[timename]>self.burn_start_time-500000)&(self.df[timename]<self.operation_end_time+500000)].copy()
        #時間調整
        self.bdf[timename] = (self.bdf[timename] - self.burn_start_time) /1000000
    
    def correct_thurst(self,after_thurst_name,before_thurst_name):
        self.df[after_thurst_name] = self.df[before_thurst_name] - self.ess

    def calcu_burn_start_time(self, timename, average_thrust_series_name):
        series = self.df[average_thrust_series_name]
        diff = series.diff() > 3
        groups = diff.groupby((diff != diff.shift()).cumsum())
        for name, group in groups:
            if group.iloc[0] and len(group) >= 10:
                start_idx = group.index[0]
                self.burn_start_time = self.df.loc[start_idx, timename]
                break
        return self.burn_start_time

    def calcu_burn_end_time(self,timename,thurstname,average_thrust_name):
        self.bdf["偏差[N]"] = self.bdf[thurstname] - self.bdf[average_thrust_name]
        self.bdf["偏差標準偏差[N]"] = self.bdf["偏差[N]"].rolling(window=100,min_periods=1).std()
        self.burn_end_time = self.bdf[(self.bdf["偏差標準偏差[N]"] <50) & (self.bdf[timename]>3)].iloc[0][timename]
        return self.burn_end_time
    
    def calcu_operation_end_time(self,timename,correct_thurst_name):
        mask = self.df[correct_thurst_name] > self.df[correct_thurst_name].max() * 0.05
        print("maxvalue", self.df[correct_thurst_name].max())
        self.operation_end_time = self.df[mask].iloc[-1][timename]
        return self.operation_end_time

    def calcu_totalimpulse(self,timename,correct_thurst_name):
        self.burn_totalimpulse = self.bdf[self.bdf[timename] < self.burn_end_time][correct_thurst_name].sum() * 0.001
        mask = self.bdf[correct_thurst_name] > self.bdf[correct_thurst_name].max() * 0.05
        self.operating_totalimpulse = self.bdf[mask][correct_thurst_name].sum() * 0.001
        self.average_thrust = self.burn_totalimpulse / (self.burn_end_time)
        return self.burn_totalimpulse,self.operating_totalimpulse

    

if __name__ == "__main__":
    datafile="2025-12-06-01/converted.csv"
    outdir="codetest/out2"
    logger_instance=Logger(datafile,outdir)
    logger_instance.fast_analysis()