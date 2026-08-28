import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import japanize_matplotlib
import numpy as np
import os

class GraphGenerator:
    def __init__(self, outdir, bdf, timename):
        self.outdir = outdir      # 出力先ディレクトリ
        self.bdf = bdf            # 燃焼データフレーム
        self.x = self.bdf[timename].values
        self.time_col_name = timename
        self.mc = 1               # 概要グラフの連番カウンタ

    def generate_general_graph(self, colname, title):
        """汎用の複数データチャンネル表示用グラフ（縦並びマルチプロット）"""
        fig, axs = plt.subplots(len(colname), 1, figsize=(12, 4 * len(colname)), squeeze=False)
        axs_flat = axs.flatten()
        for i in range(len(colname)):
            y = self.bdf[colname[i]].values
            axs_flat[i].plot(self.x, y, linewidth=0.5)
            axs_flat[i].set_title(colname[i])
            axs_flat[i].set_xlabel("時間(s)")
            axs_flat[i].set_ylabel(colname[i])
            axs_flat[i].grid(which='major', lw=0.7)

            # 主目盛に対し、補助目盛の細かさを設定
            axs_flat[i].xaxis.set_minor_locator(ticker.AutoMinorLocator(10))
            axs_flat[i].yaxis.set_minor_locator(ticker.AutoMinorLocator(5))
            axs_flat[i].grid(which='minor', lw=0.4)

        plt.tight_layout()
        plt.savefig(os.path.join(self.outdir, title), dpi=100)
        plt.close(fig)

    def generate_graph_from_series(self, x_series, y_series, title):
        """シリーズデータを直接渡して出力するグラフ"""
        fig, ax = plt.subplots()
        ax.plot(x_series, y_series)
        ax.set_title(title)
        ax.set_xlabel("時間(s)")
        ax.set_ylabel(title)
        ax.grid(True)

        plt.savefig(os.path.join(self.outdir, f"{title}.png"))
        plt.close(fig)
        
    def generate_overview_graph(self, timename, thrust_name, pressure_name, burnend, opend, operating_totalimpulse, burn_totalimpulse, date):
        """推力・圧力を統合し、開始・終了境界とインパルステキストを重ねた概要グラフ"""
        x = self.bdf[timename].values
        fig, ax1 = plt.subplots(figsize=(12, 6))
        
        # 左Y軸: 推力
        ax1.set_xlabel('時間(s)')
        ax1.set_ylabel(thrust_name)
        ax1.plot(x, self.bdf[thrust_name].values, color="tab:blue", linewidth=2, label=thrust_name)
        ax1.grid(True, alpha=0.3)
        
        # 右Y軸: 圧力
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
        
        # 燃焼終了時間・作動終了時間の垂直線
        ax1.axvline(x=burnend, color='red', linewidth=2, label=f'燃焼終了時間({burnend:.3f} s)')
        ax1.axvline(x=opend, color='blue', linewidth=2, label=f'作動終了時間({opend:.3f} s)')
        
        # 凡例の統合
        lines1, labels1 = ax1.get_legend_handles_labels()
        if pressure_name is not None:
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
        else:
            ax1.legend(lines1, labels1, loc='upper right')

        # トータルインパルス値を凡例の下付近に追加
        textstr = f'作動時間トータルインパルス: {operating_totalimpulse:.2f} N·s\n燃焼トータルインパルス: {burn_totalimpulse:.2f} N·s'
        ax1.text(0.98, 0.8, textstr, transform=ax1.transAxes, fontsize=10,
                 verticalalignment='top', horizontalalignment='right', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        fig.tight_layout()
        safe_thrust_name = thrust_name.replace("/", "／")
        if pressure_name is not None:
            safe_p_names = [p.replace("/", "／") for p in pressures]
            safe_pressure_name = "_".join(safe_p_names)
            plt.savefig(os.path.join(self.outdir, f"{safe_thrust_name}_{safe_pressure_name}.png"))
        else:
            plt.savefig(os.path.join(self.outdir, f"{safe_thrust_name}_のみ.png"))
        
        self.mc += 1
        plt.close(fig)

    def generate_thrust_heatmap(self, col_name, burn_end_time, output_path, vmin=-40, vmax=40, is_pressure=False):
        """
        燃焼中の推力・圧力データを0.1秒ごとに区切り、FFTを用いて周波数解析したヒートマップ画像を生成する。
        """
        time_col = self.time_col_name
        df_burn = self.bdf[(self.bdf[time_col] >= 0) & (self.bdf[time_col] <= burn_end_time)].copy()

        # データ不足時のガード
        if len(df_burn) < 10 or burn_end_time < 0.1:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, "周波数解析に必要なデータ長が不足しています", ha='center', va='center', fontsize=12)
            ax.set_title(f"{col_name}の周波数解析ヒートマップ (FFT 0.1秒区間)", fontsize=13, fontweight='bold')
            plt.tight_layout()
            plt.savefig(output_path, dpi=150)
            plt.close(fig)
            return

        # サンプリング周波数 fs の推定
        times = df_burn[time_col].values
        dt = np.median(np.diff(times))
        if dt <= 0 or np.isnan(dt):
            dt = 0.001
        fs = 1.0 / dt

        window_duration = 0.1
        N_window = int(round(window_duration * fs))
        if N_window < 4:
            N_window = 4

        N_fft = 512
        if N_fft < N_window:
            N_fft = int(2 ** np.ceil(np.log2(N_window)))

        t_starts = np.arange(0, burn_end_time - window_duration + 1e-9, window_duration)
        if len(t_starts) == 0:
            t_starts = np.array([0.0])

        fft_matrix = []
        times_centers = []

        for t_start in t_starts:
            t_interp = np.linspace(t_start, t_start + window_duration, N_window, endpoint=False)
            thrust_interp = np.interp(t_interp, df_burn[time_col].values, df_burn[col_name].values)
            
            # 圧力の場合はPaからkPaへ変換
            if is_pressure:
                thrust_interp = thrust_interp / 1000.0
                
            thrust_detrend = thrust_interp - np.mean(thrust_interp)
            
            window = np.hanning(N_window)
            thrust_windowed = thrust_detrend * window
            
            fft_vals = np.fft.rfft(thrust_windowed, n=N_fft)
            amplitude = np.abs(fft_vals) * (2.0 / N_window)
            # 振幅をデシベル(dB)に変換 (基準: 1.0 N または 1.0 kPa)
            amplitude_db = 20 * np.log10(np.maximum(amplitude, 1e-5))
            
            fft_matrix.append(amplitude_db)
            times_centers.append(t_start + window_duration / 2.0)

        fft_matrix = np.array(fft_matrix)
        frequencies = np.fft.rfftfreq(N_fft, d=(1.0 / fs))
        times_centers = np.array(times_centers)

        # 描画処理
        fig, ax = plt.subplots(figsize=(10, 6))
        X, Y = np.meshgrid(frequencies, times_centers)
        mesh = ax.pcolormesh(X, Y, fft_matrix, shading='auto', cmap='inferno', vmin=vmin, vmax=vmax)
        cbar = fig.colorbar(mesh, ax=ax)
        
        unit = "dB (ref: 1 kPa)" if is_pressure else "dB (ref: 1 N)"
        cbar.set_label(f'{col_name}振幅 [{unit}]', fontsize=11)
        
        # サンプリング周波数に応じた表示範囲 (0〜ナイキスト周波数 fs/2 Hz)
        max_freq = fs / 2.0
        ax.set_xlim(0, max_freq)

        if max_freq <= 500:
            major_step, minor_step = 50, 10
        elif max_freq <= 1000:
            major_step, minor_step = 100, 20
        else:
            major_step, minor_step = 200, 50

        ax.xaxis.set_major_locator(ticker.MultipleLocator(major_step))
        ax.xaxis.set_minor_locator(ticker.MultipleLocator(minor_step))
        
        ax.set_xlabel('周波数 [Hz]', fontsize=11)
        ax.set_ylabel('時間 [s]', fontsize=11)
        ax.set_title(f'{col_name}の周波数解析ヒートマップ (FFT 0.1秒区間)', fontsize=13, fontweight='bold')
        ax.grid(which='major', linestyle='--', alpha=0.5, color='gray')
        ax.grid(which='minor', linestyle=':', alpha=0.3, color='gray')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close(fig)

    def generate_stacked_thrust_pressure_graph(self, filename="推力_燃焼室圧_タンク圧.png"):
        """
        補正推力、燃焼室圧、タンク圧を縦に並べた3段グラフを作成する。
        圧力1と圧力2のうち、燃焼開始時(x=0付近)に圧力が3MPa(3,000,000 Pa)以上ある方をタンク圧、
        もう一方を燃焼室圧として判定する。
        """
        idx_start = (np.abs(self.x - 0.0)).argmin()
        
        p1_col = "圧力1[Pa]"
        p2_col = "圧力2[Pa]"
        thrust_col = "補正推力[N]"
        
        tank_col = None
        chamber_col = None
        
        if p1_col in self.bdf.columns and p2_col in self.bdf.columns:
            p1_val = self.bdf[p1_col].iloc[idx_start]
            p2_val = self.bdf[p2_col].iloc[idx_start]
            
            # 3MPa = 3,000,000 Pa
            if p1_val >= 3000000.0 and p2_val < 3000000.0:
                tank_col = p1_col
                chamber_col = p2_col
            elif p2_val >= 3000000.0 and p1_val < 3000000.0:
                tank_col = p2_col
                chamber_col = p1_col
            elif p1_val >= 3000000.0 and p2_val >= 3000000.0:
                if p1_val >= p2_val:
                    tank_col = p1_col
                    chamber_col = p2_col
                else:
                    tank_col = p2_col
                    chamber_col = p1_col
            else:
                if p1_val >= p2_val:
                    tank_col = p1_col
                    chamber_col = p2_col
                else:
                    tank_col = p2_col
                    chamber_col = p1_col
        elif p1_col in self.bdf.columns:
            chamber_col = p1_col
        elif p2_col in self.bdf.columns:
            tank_col = p2_col

        fig, axs = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
        
        # 1段目: 補正推力
        if thrust_col in self.bdf.columns:
            axs[0].plot(self.x, self.bdf[thrust_col].values, color="tab:blue", linewidth=0.8)
            axs[0].set_ylabel(thrust_col)
        else:
            axs[0].set_ylabel("推力[N]")
        axs[0].set_title("推力", fontsize=12, fontweight='bold')
        axs[0].grid(which='major', lw=0.7)
        axs[0].xaxis.set_minor_locator(ticker.AutoMinorLocator(10))
        axs[0].yaxis.set_minor_locator(ticker.AutoMinorLocator(5))
        axs[0].grid(which='minor', lw=0.4)

        # 2段目: 燃焼室圧
        if chamber_col and chamber_col in self.bdf.columns:
            axs[1].plot(self.x, self.bdf[chamber_col].values, color="tab:orange", linewidth=0.8)
            axs[1].set_ylabel(chamber_col)
        else:
            axs[1].set_ylabel("圧力[Pa]")
        axs[1].set_title("燃焼室圧", fontsize=12, fontweight='bold')
        axs[1].grid(which='major', lw=0.7)
        axs[1].xaxis.set_minor_locator(ticker.AutoMinorLocator(10))
        axs[1].yaxis.set_minor_locator(ticker.AutoMinorLocator(5))
        axs[1].grid(which='minor', lw=0.4)

        # 3段目: タンク圧
        if tank_col and tank_col in self.bdf.columns:
            axs[2].plot(self.x, self.bdf[tank_col].values, color="tab:green", linewidth=0.8)
            axs[2].set_ylabel(tank_col)
        else:
            axs[2].set_ylabel("圧力[Pa]")
        axs[2].set_title("タンク圧", fontsize=12, fontweight='bold')
        axs[2].set_xlabel("時間(s)")
        axs[2].grid(which='major', lw=0.7)
        axs[2].xaxis.set_minor_locator(ticker.AutoMinorLocator(10))
        axs[2].yaxis.set_minor_locator(ticker.AutoMinorLocator(5))
        axs[2].grid(which='minor', lw=0.4)

        plt.tight_layout()
        plt.savefig(os.path.join(self.outdir, filename), dpi=100)
        plt.close(fig)

