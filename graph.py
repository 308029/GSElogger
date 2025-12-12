import pandas as pd
import matplotlib.pyplot as plt
import japanize_matplotlib
import os

os.makedirs("codetest/out", exist_ok=True)
datafile = "codetest/short.csv"  
outdir = "codetest/out"  

def data2graph(datafile,outdir,cut=True):
    data=pd.read_csv(datafile,header=0)
    data.reset_index(inplace=True)
    data=data.shift(axis=1)
    data["index"]=0
    print(data)

    cdata = data.copy()
    #中央値
    mmedian = cdata["推力[N]"].median()
    print(mmedian)
    mdf =  cdata[cdata["推力[N]"] > 180].copy()
    #時間調整
    mdf["データ取得開始時"] = mdf["データ取得開始時"] - mdf["データ取得開始時"].iloc[0]
    mdf["データ取得開始時"] = mdf["データ取得開始時"] /1000000
    ml = ["推力[N]","圧力1[Pa]","圧力2[Pa]","圧力3[Pa]","圧力4[Pa]","低域温度1","低域温度2","低域温度3","高域温度1","高域温度2"]

    if cut:
        #全体の推力も保存
        plt.figure()
        y = data["推力[N]"].values
        x = data["データ取得開始時"].values
        plt.plot(x, y)
        plt.title("全体推力[N]")
        plt.xlabel("時間(s)")
        plt.ylabel("推力[N]")
        plt.grid(True)
        plt.savefig(outdir + "/" + "全体推力[N].png")

    for i in range(10):
        plt.figure()
        y = mdf[ml[i]].values
        x = mdf["データ取得開始時"].values

        # グラフ描画
        plt.plot(x, y)

        # タイトルとラベル
        plt.title(ml[i])
        plt.xlabel("時間(s)")
        plt.ylabel(ml[i])

        # グリッド
        plt.grid(True)

        # 保存
        plt.savefig(outdir + "/" + ml[i] + ".png")

if __name__ == "__main__":
    data2graph(datafile, outdir)