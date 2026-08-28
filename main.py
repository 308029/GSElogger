from raw_converter import RawDataConverter
from thrust_analyzer import ThrustAnalyzer
from graph_generator import GraphGenerator
import pandas
import os
import time

maindir = "2026-05-09-2"
rawfile ="LOG1.csv" #old logger LOG-0000001.csv new logger LOG.csv
redatafile = "converted.csv"

outdir = "report"
mode="full" #full or manual
loadcell_max_lbf=500 #250 500 1000
loggertype="new" # new or old
#!稼働時間表示
#manual mode settings
starttime = 1750000000
endtime = 2030000000

date = maindir 
abrawfile = os.path.join(maindir,rawfile)
abredatafile = os.path.join(maindir,redatafile)
aboutdir = os.path.join(maindir,outdir)

#出力フォルダがなかったら作る
os.makedirs(aboutdir, exist_ok=True)
#解析
print("Analysing raw data...")
start = time.time()
RawDataConverter(abrawfile, abredatafile,loadcell_max_lbf,loggertype).convert()
rawconvert_time = time.time() - start

if loggertype == "new":
    temp_cols = ["温度1[℃]", "温度2[℃]", "温度3[℃]", "温度4[℃]", "温度5[℃]", "温度6[℃]"]
else:
    temp_cols = ["低域温度1[℃]", "低域温度2[℃]", "低域温度3[℃]", "高域温度1[℃]", "高域温度2[℃]"]

ml = ["推力[N]","補正推力[N]","平均推力[N]","偏差標準偏差[N]","圧力1[Pa]","圧力2[Pa]","圧力3[Pa]","圧力4[Pa]"] + temp_cols
if mode=="full":
    logger = ThrustAnalyzer(abredatafile, aboutdir,"データ取得開始時","推力[N]")

    start = time.time()
    print("Analysing converted data...")
    analyzing_time = time.time() - start

    exportcsv = logger.bbdf
    exportcsv.to_csv(os.path.join(aboutdir,"operationthurst.csv"), index=False, header=False)
    print("----------")
    print("定常偏差",round(logger.ess,1),"N")
    print("燃焼終了時間",logger.burn_end_time,"s")
    print("作動終了時間",(logger.operation_end_time - logger.burn_start_time)/1000000,"s")
    total,op,avg = logger.calcu_totalimpulse("補正推力[N]")
    print("トータルインパルス",round(total,1),"N・s")
    print("作動時間トータルインパルス",round(op,1),"N・s")
    print("----------")

    graph = GraphGenerator(aboutdir, logger.bdf, "データ取得開始時")
    print("Creating graphs...")
    start = time.time()
    graph.generate_graph_from_series(logger.df["データ取得開始時"][::1000],logger.df["推力[N]"][::1000],"全体推力[N]")
    graph.generate_general_graph(["推力[N]","補正推力[N]","平均推力[N]","偏差標準偏差[N]"],"推力関連.png")
    graph.generate_general_graph(["圧力1[Pa]","圧力2[Pa]","圧力3[Pa]","圧力4[Pa]"],"圧力.png")
    graph.generate_general_graph(temp_cols,"温度.png")
    graph.generate_stacked_thrust_pressure_graph("推力_燃焼室圧_タンク圧.png")
    generate_graph_time = time.time() - start

    operationendrelative = (logger.operation_end_time - logger.burn_start_time)/1000000
    graph.generate_overview_graph("データ取得開始時","推力[N]",["圧力1[Pa]"],logger.burn_end_time,operationendrelative,logger.operating_totalimpulse, logger.burn_totalimpulse,date)
    graph.generate_overview_graph("データ取得開始時","平均推力[N]",["平均圧力1[Pa]"],logger.burn_end_time,operationendrelative,logger.operating_totalimpulse,logger.burn_totalimpulse,date)
    graph.generate_overview_graph("データ取得開始時","補正推力[N]",None,logger.burn_end_time,operationendrelative,logger.operating_totalimpulse,logger.burn_totalimpulse,date)

    # 周波数解析ヒートマップの生成
    print("Creating frequency analysis heatmaps...")
    heatmap_path = os.path.join(aboutdir, "推力周波数解析ヒートマップ.png")
    graph.generate_thrust_heatmap("推力[N]", logger.burn_end_time, heatmap_path, vmin=-40, vmax=40, is_pressure=False)

    for i in range(1, 5):
        p_col = f"圧力{i}[Pa]"
        if p_col in logger.bdf.columns:
            p_heatmap_path = os.path.join(aboutdir, f"圧力{i}_周波数解析ヒートマップ.png")
            graph.generate_thrust_heatmap(p_col, logger.burn_end_time, p_heatmap_path, vmin=-40, vmax=40, is_pressure=True)

    print("raw解析時間: {}s\nデータ分析時間: {}s \nグラフ生成時間: {}s".format(rawconvert_time, analyzing_time, generate_graph_time))
elif mode=="manual":
    print("Manual mode generationg graph...")
    ccsv = pandas.read_csv(abredatafile)
    if(starttime is not None):
        ccsv=ccsv[(ccsv["データ取得開始時"]>=starttime)]
    if(endtime is not None):
        ccsv=ccsv[(ccsv["データ取得開始時"]<=endtime)]
    
    graph = GraphGenerator(aboutdir, ccsv, "データ取得開始時")
    # graph.generate_graph_from_series()
    graph.generate_general_graph(["推力[N]"],"推力.png")
    graph.generate_general_graph(["圧力1[Pa]","圧力2[Pa]","圧力3[Pa]","圧力4[Pa]"],"圧力.png")
    graph.generate_general_graph(temp_cols,"温度.png")