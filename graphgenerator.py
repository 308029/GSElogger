import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import japanize_matplotlib
import os

class graph_generator:
    def __init__(self, outdir, bdf, timename):
        self.outdir = outdir #出力ディレクトリ
        self.bdf = bdf #燃焼データフレーム
        self.x = self.bdf[timename].values

        self.mc = 1 #overview graph用の連番

    def generate_general_graph(self, colname, title):
        # 2x2の計4枚を1枚にまとめる例
        fig, axs = plt.subplots(len(colname),1, figsize=(12, 4 * len(colname)), squeeze=False)
        # axsは2次元配列になるので平坦化するとループしやすい
        axs_flat = axs.flatten()
        for i in range(len(colname)):
            y = self.bdf[colname[i]].values
            axs_flat[i].plot(self.x, y, linewidth=0.5)
            axs_flat[i].set_title(colname[i])
            axs_flat[i].set_xlabel("時間(s)")
            axs_flat[i].set_ylabel(colname[i])

            axs_flat[i].grid(which='major', lw=0.7) # 主目盛の描画(標準)

            # X,Y軸に対して、(補助目盛)×5 = (主目盛)
            axs_flat[i].xaxis.set_minor_locator(ticker.AutoMinorLocator(10))
            axs_flat[i].yaxis.set_minor_locator(ticker.AutoMinorLocator(5))
            axs_flat[i].grid(which='minor', lw=0.4) # 補助目盛の描画

        plt.tight_layout()
        plt.savefig(os.path.join(self.outdir, title), dpi=100)
        plt.close(fig)

    def generate_graph_from_series(self,x_series,y_series,title):

        # グラフ描画
        plt.plot(x_series, y_series)
        # タイトルとラベル
        plt.title(title)
        plt.xlabel("時間(s)")
        plt.ylabel(y_series)

        # グリッド
        plt.grid(True)

        # 保存
        plt.savefig(self.outdir + "/" + title + ".png")
        plt.close()
        
    def generate_overview_graph(self, timename,thurst_name,pressure_name, burnend, opend,operationgtotalimpulse, burntotalimpulse,date):
        x = self.bdf[timename].values
        # 平均推力と圧力1、圧力2をtwinxで重ねて表示
        fig, ax1 = plt.subplots(figsize=(12, 6))
        
        # 左Y軸：平均推力
        ax1.set_xlabel('時間(s)')
        ax1.set_ylabel(thurst_name)
        ax1.plot(x, self.bdf[thurst_name].values, color="tab:blue", linewidth=2, label=thurst_name)
        # ax1.tick_params(axis='y', labelcolor="blue")
        ax1.grid(True, alpha=0.3)
        
        # 右Y軸：圧力
        if pressure_name is not None:
            if isinstance(pressure_name, str):
                pressures = [pressure_name]
            else:
                pressures = list(pressure_name)
                
            ax2 = ax1.twinx()
            ax2.set_ylabel('圧力[Pa]')
            colors = ['orange', 'green', 'red', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
            for idx, p_col in enumerate(pressures):
                color = colors[idx % len(colors)]
                ax2.plot(x, self.bdf[p_col].values, color=color, label=p_col, alpha=0.5)
            
        # タイトルと凡例
        if pressure_name is not None:
            plt.title('推力と圧力データ({})'.format(date))
        else:
            plt.title('推力データ({})'.format(date))
        
        # burnend時間に赤い縦線を引く
        ax1.axvline(x=burnend, color='red', linewidth=2, label=f'燃焼終了時間({burnend:.3f})')
        ax1.axvline(x=opend, color='blue', linewidth=2, label=f'作動終了時間({opend:.3f})')
        
        # 凡例を統合
        lines1, labels1 = ax1.get_legend_handles_labels()
        if pressure_name is not None:
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
        else:
            ax1.legend(lines1, labels1, loc='upper right')

        # トータルインパルスの値をテキストで追加（右上、凡例の下）
        textstr = f'作動時間トータルインパルス: {operationgtotalimpulse:.2f} N·s\n燃焼トータルインパルス: {burntotalimpulse:.2f} N·s'
        ax1.text(0.98, 0.8, textstr, transform=ax1.transAxes, fontsize=10,
                verticalalignment='top', horizontalalignment='right', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        fig.tight_layout()
        safe_thurst_name = thurst_name.replace("/", "／")
        if pressure_name is not None:
            safe_p_names = [p.replace("/", "／") for p in pressures]
            safe_pressure_name = "_".join(safe_p_names)
            plt.savefig(os.path.join(self.outdir, f"{safe_thurst_name}_{safe_pressure_name}.png"))
        else:
            plt.savefig(os.path.join(self.outdir, f"{safe_thurst_name}_のみ.png"))
        self.mc += 1
        plt.close()
