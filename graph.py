import pandas as pd
import matplotlib.pyplot as plt
import japanize_matplotlib

# df=pd.read_csv("oo.csv")

def data2graph(datafile,outdir,starttime=None,endtime=None):
    data=pd.read_csv(datafile,header=0)
    data.reset_index(inplace=True)
    data=data.shift(axis=1)
    data["index"]=0

    mdf = data
    if(starttime is not None):
        mdf=mdf[(mdf["データ取得開始時"]>=starttime)]
    if(endtime is not None):
        mdf=mdf[(mdf["データ取得開始時"]<=endtime)]

    ml = ["推力[N]","圧力1[Pa]","圧力2[Pa]","圧力3[Pa]","圧力4[Pa]","低域温度1","低域温度2","低域温度3","高域温度1","高域温度2"]
    for i in range(10):
        plt.figure()
        y = mdf[ml[i]].values
        x = mdf["データ取得開始時"].values

        # グラフ描画
        plt.plot(x, y)

        # タイトルとラベル
        plt.title(ml[i])
        plt.xlabel("時間")
        plt.ylabel(ml[i])

        # グリッド
        plt.grid(True)

        # 保存
        plt.savefig(outdir + "/" + ml[i] + ".png")
