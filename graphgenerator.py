import matplotlib.pyplot as plt
import japanize_matplotlib

class graph_generator:
    def __init__(self, outdir):
        self.outdir = outdir #出力ディレクトリ
        self.bdf = None #燃焼データフレーム

    def generate_general_graph(self,timename, colname):
        x = self.bdf[timename].values
        plt.figure()
        y = self.bdf[colname].values

        # グラフ描画
        plt.plot(x, y)
        # タイトルとラベル
        plt.title(colname)
        plt.xlabel("時間(s)")
        plt.ylabel(colname)

        # グリッド
        plt.grid(True)

        # 保存
        plt.savefig(self.outdir + "/" + colname + ".png")
        plt.close()

    def generate_overview_graph(self, timename,average_thurst_name,pressure_1_name,pressure_2_name, burnend, operationgtotalimpulse, burntotalimpulse):
        x = self.bdf[timename].values
        # 平均推力と圧力1、圧力2をtwinxで重ねて表示
        fig, ax1 = plt.subplots(figsize=(12, 6))
        
        # 左Y軸：平均推力
        color1 = 'tab:blue'
        ax1.set_xlabel('時間(s)')
        ax1.set_ylabel(average_thurst_name)
        ax1.plot(x, self.bdf[average_thurst_name].values, color=color1, linewidth=2, label='平均推力[N]')
        ax1.tick_params(axis='y', labelcolor=color1)
        ax1.grid(True, alpha=0.3)
        
        # 右Y軸：圧力1、圧力2
        ax2 = ax1.twinx()
        color2 = 'tab:orange'
        color3 = 'tab:green'
        ax2.set_ylabel('圧力[Pa]')
        ax2.plot(x, self.bdf[pressure_1_name].values, color='orange', label=pressure_1_name)
        ax2.plot(x, self.bdf[pressure_2_name].values, color='green', label=pressure_2_name)

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
        plt.savefig(self.outdir + "/" + "平均推力と圧力比較.png")
        plt.close()
