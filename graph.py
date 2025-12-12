import pandas as pd
import matplotlib.pyplot as plt
import japanize_matplotlib
import os

#maxvalue 780488 のとき992.3532N
def calcu_moving_ave(targetrow):
    return  targetrow.rolling(window=100,min_periods=1).mean()

def data2graph(datafile,outdir,cut=True):
    data=pd.read_csv(datafile,header=0)
   #平均曲線
    data["平均推力[N]"] = calcu_moving_ave(data["推力[N]"])
    data["平均圧力1[Pa]"] = calcu_moving_ave(data["圧力1[Pa]"])
    data["平均圧力2[Pa]"] = calcu_moving_ave(data["圧力2[Pa]"])

    #中央値
    mmedian = data["平均推力[N]"].median()
    print(mmedian)
    burnstart = data[data["平均推力[N]"] > mmedian+20].iloc[0]["データ取得開始時"]
     
    mdf=data[(data["データ取得開始時"]>burnstart-500000)&(data["データ取得開始時"]<burnstart+8000000)&(data["推力[N]"]>mmedian+10)].copy()
    #時間調整
    mdf["データ取得開始時"] = (mdf["データ取得開始時"] - burnstart) /1000000

    #燃焼終了
    mdf["偏差[N]"] = mdf["推力[N]"] - mdf["平均推力[N]"]
    mdf["偏差標準偏差[N]"] = mdf["偏差[N]"].rolling(window=100,min_periods=1).std()
    burnend = mdf[(mdf["偏差標準偏差[N]"] <50) & (mdf["データ取得開始時"]>3)].iloc[0]["データ取得開始時"]
    print(burnend)
    #トータルインパルス
    mdf["補正推力[N]"] = mdf["推力[N]"] - mmedian

    burntotalimpulse = mdf[mdf["データ取得開始時"] < burnend]["補正推力[N]"].sum() * 0.001
    operationgtotalimpulse = mdf[mdf["補正推力[N]"] > mdf["補正推力[N]"].max()*0.05]["補正推力[N]"].sum() * 0.001
    print("作動時間トータルインパルス:",operationgtotalimpulse)
    print("燃焼トータルインパルス:",burntotalimpulse)
    
    
    ml = ["推力[N]","圧力1[Pa]","圧力2[Pa]","圧力3[Pa]","圧力4[Pa]","低域温度1","低域温度2","低域温度3","高域温度1","高域温度2"]
    
    #total thrust
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
        plt.close()
    
   

    x = mdf["データ取得開始時"].values

    # 平均推力と圧力1、圧力2をtwinxで重ねて表示
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # 左Y軸：平均推力
    color1 = 'tab:blue'
    ax1.set_xlabel('時間(s)')
    ax1.set_ylabel('平均推力[N]')
    ax1.plot(x, mdf["平均推力[N]"].values, color=color1, linewidth=2, label='平均推力[N]')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, alpha=0.3)
    
    # 右Y軸：圧力1、圧力2
    ax2 = ax1.twinx()
    color2 = 'tab:orange'
    color3 = 'tab:green'
    ax2.set_ylabel('圧力[Pa]')
    ax2.plot(x, mdf["平均圧力1[Pa]"].values, color='orange', label='平均圧力1[Pa]')
    ax2.plot(x, mdf["平均圧力2[Pa]"].values, color='green', label='平均圧力2[Pa]')
    
    # タイトルと凡例
    plt.title('平均推力と圧力1、圧力2の比較')
    
    # burnend時間に赤い縦線を引く
    ax1.axvline(x=burnend, color='red', linewidth=2, label='燃焼終了時間')
    
    # burnendの値をx軸に表示
    ax1.text(burnend, ax1.get_ylim()[0], f'{burnend:.2f}s', ha='center', va='top', 
             fontsize=10, color='red', fontweight='bold',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # 凡例を統合
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    # トータルインパルスの値をテキストで追加（右上、凡例の下）
    textstr = f'作動時間トータルインパルス: {operationgtotalimpulse:.2f} N·s\n燃焼トータルインパルス: {burntotalimpulse:.2f} N·s'
    ax1.text(0.98, 0.65, textstr, transform=ax1.transAxes, fontsize=10,
             verticalalignment='top', horizontalalignment='right', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    fig.tight_layout()
    plt.savefig(outdir + "/" + "平均推力と圧力比較.png")
    plt.show()
    plt.close()

    for colname in ml:
        plt.figure()
        y = mdf[colname].values

        # グラフ描画
        plt.plot(x, y)
        if colname == "推力[N]":
            plt.plot(x, mdf["偏差[N]"].values,color="orange")
        # タイトルとラベル
        plt.title(colname)
        plt.xlabel("時間(s)")
        plt.ylabel(colname)

        # グリッド
        plt.grid(True)

        # 保存
        plt.savefig(outdir + "/" + colname + ".png")
        plt.close()

if __name__ == "__main__":
    outdir = "codetest/out1"  
    os.makedirs(outdir, exist_ok=True)
    datafile = "2025-12-06-02/converted.csv"  
    data2graph(datafile, outdir)