# Logger クラス関数リファレンス

対象ファイル: `dataanlysis.py`（※ファイル名は `dataanalysis.py` ではなく `dataanlysis.py`）

## クラス概要
`Logger` は CSV ログを読み込み、推力・圧力の移動平均、燃焼開始/終了時刻、補正推力、トータルインパルスを計算するクラスです。

## メソッド一覧

### `__init__(self, data_file, out_dir, time_name, thrust_name)`
- 役割: 初期化と一連の前処理/解析の実行。
- 引数:
  - `data_file` (`str`): 入力 CSV パス
  - `out_dir` (`str`): 出力先ディレクトリ（現状このクラス内では未使用）
  - `time_name` (`str`): 時刻列名
  - `thrust_name` (`str`): 推力列名
- 戻り値: なし
- 主な副作用:
  - `self.df` に CSV を読み込み
  - 推力/圧力の移動平均列を追加
  - `burn_start_time`, `ess`, `operation_end_time`, `burn_end_time` などを計算
  - `self.bdf`（燃焼区間 DataFrame）を生成
- 例外: CSV 読み込み失敗時は `pandas` 由来の例外が発生

### `calcu_moving_ave(self, before_series, after_series)`
- 役割: 指定列の移動平均（window=100）を計算し、新列として追加。
- 引数:
  - `before_series` (`str`): 元列名
  - `after_series` (`str`): 追加先列名
- 戻り値: なし
- 備考: `min_periods=1` のため先頭から値が入る。

### `calcu_thrust_ess(self)`
- 役割: 燃焼開始前データの推力中央値を定常偏差 `ess` として算出。
- 引数: なし
- 戻り値: `ess`（数値）
- 例外:
  - `burn_start_time` が未設定の場合 `ValueError`

### `create_burndata(self)`
- 役割: 燃焼開始前後 ±500000 μs の区間を切り出して `self.bdf` を作成。
- 引数: なし
- 戻り値: なし
- 主な副作用:
  - `self.bdf` を作成
  - `self.bdf[time_name]` を「燃焼開始基準の秒」に変換

### `correct_thurst(self, after_thurst_name)`
- 役割: 推力から定常偏差 `ess` を引いた補正推力列を追加。
- 引数:
  - `after_thurst_name` (`str`): 追加先列名
- 戻り値: なし
- 備考: メソッド名・引数名の `thurst` は実装上のスペル（thrust の誤記）。

### `calcu_burn_start_time(self, average_thrust_series_name)`
- 役割: 移動平均推力の差分が `>1` の状態が 10 サンプル以上連続する最初の時刻を燃焼開始時刻として返す。
- 引数:
  - `average_thrust_series_name` (`str`): 判定対象の平均推力列名
- 戻り値: `burn_start_time`（元データ時刻スケール）
- 備考:
  - 条件を満たさない場合は `0` を返す実装。

### `calcu_burn_end_time(self, average_thrust_name)`
- 役割: 燃焼区間データで偏差標準偏差を計算し、`偏差標準偏差[N] > 10` を満たす最後の時刻を燃焼終了時刻として返す。
- 引数:
  - `average_thrust_name` (`str`): 平均推力列名
- 戻り値: `burn_end_time`（`create_burndata` 後の時刻スケール、秒）
- 前提: `self.bdf` が作成済みであること

### `calcu_operation_end_time(self, correct_thurst_name)`
- 役割: 補正推力が最大値の 5% を超える最後の時刻を作動終了時刻として返す。
- 引数:
  - `correct_thurst_name` (`str`): 補正推力列名
- 戻り値: `operation_end_time`（元データ時刻スケール）
- 備考: 最大推力を標準出力に表示する。

### `calcu_totalimpulse(self, correct_thurst_name)`
- 役割: 燃焼区間トータルインパルス、作動区間トータルインパルス、平均推力を算出。
- 引数:
  - `correct_thurst_name` (`str`): 補正推力列名
- 戻り値:
  - `burn_totalimpulse`
  - `operating_totalimpulse`
  - `average_thrust`
- 算出式:
  - `burn_totalimpulse = sum(燃焼終了時刻未満の補正推力) * 0.001`
  - `operating_totalimpulse = sum(補正推力 > 最大値×0.05) * 0.001`
  - `average_thrust = burn_totalimpulse / burn_end_time`
- 前提: `self.bdf` と `self.burn_end_time` が設定済みであること

## 利用上の注意
- 初期化時に多くの計算が自動実行されるため、入力 CSV の列名不一致があると途中で失敗します。
- `__main__` のサンプル呼び出しは現行シグネチャと一致していません（`time_name`, `thrust_name` が不足）。
