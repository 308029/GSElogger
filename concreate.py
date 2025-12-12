import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def plot_csv_column(csv_file, col_name=None, col_index=0):
    """
    CSVファイルの指定された列をグラフにプロット
    
    Args:
        csv_file (str): CSVファイルのパス
        col_name (str): プロットする列の名前（指定されない場合は col_index を使用）
        col_index (int): プロットする列のインデックス（デフォルト0）
    """
    # CSVファイルを読み込む
    df = pd.read_csv(csv_file)
    
    # 指定された列を取得
    if col_name is not None:
        if col_name not in df.columns:
            print(f"エラー: 列 '{col_name}' はファイルに存在しません")
            print(f"利用可能な列: {list(df.columns)}")
            return
        column = df[col_name]
    else:
        if col_index >= len(df.columns):
            print(f"エラー: 列インデックス {col_index} はファイルに存在しません")
            return
        column = df.iloc[:, col_index]
    
    # グラフを作成
    plt.figure(figsize=(12, 6))
    
    # 数値データのみを抽出
    numeric_data = pd.to_numeric(column, errors='coerce')
    numeric_data = numeric_data.dropna()
    
    if len(numeric_data) == 0:
        print("プロットする数値データがありません")
        return
    
    # グラフをプロット
    plt.plot(numeric_data.values)
    plt.xlabel('行番号')
    plt.ylabel('値')
    plt.title(f'CSVファイルの列データ: {column.name}')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # グラフを表示
    plt.show()

if __name__ == "__main__":
    # 使用例
    csv_file = "human/concreate2.csv"  # 変更が必要な場合はここを修正
    plot_csv_column(csv_file, col_index=3)  # 0番目の列を表示
    # plot_csv_column(csv_file, col_name="列の名前")  # 列の名前で指定することも可能
