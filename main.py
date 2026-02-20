from analysis import RawConverter#!
from dataanlysis import Logger
from graphgenerator import graph_generator
import pandas
import os
import time

maindir = "logger試験"
rawfile ="LOG.csv" #old logger LOG-0000001.csv new logger LOG.csv
redatafile = "converted4.csv"

outdir = "out4"
mode="manual" #full or fast or manual
loadcell_max_lbf=500 #250 500 1000
loggertype="new" # new or old
#!稼働時間表示
#manual mode settings
starttime = None
endtime = None

date = maindir
abrawfile = os.path.join(maindir,rawfile)
abredatafile = os.path.join(maindir,redatafile)
aboutdir = os.path.join(maindir,outdir)

#出力フォルダがなかったら作る
os.makedirs(aboutdir, exist_ok=True)
#解析
print("Analysing raw data...")
start = time.time()
RawConverter(abrawfile, abredatafile,loadcell_max_lbf,loggertype).convert()
rawconvert_time = time.time() - start

logger = Logger(abredatafile, aboutdir,"データ取得開始時","推力[N]")


ml = ["推力[N]","補正推力[N]","平均推力[N]","偏差標準偏差[N]","圧力1[Pa]","圧力2[Pa]","圧力3[Pa]","圧力4[Pa]","低域温度1[℃]","低域温度2[℃]","低域温度3[℃]","高域温度1[℃]","高域温度2[℃]"]

if mode=="fast":
    print("Analysing converted data...")
    logger.calcu_moving_ave("推力[N]","平均推力[N]")
   
    logger.calcu_burn_start_time("平均推力[N]")
    logger.calcu_thrust_ess()
    logger.correct_thurst("補正推力[N]")
    logger.calcu_operation_end_time("補正推力[N]")
    logger.create_burndata()
    logger.calcu_burn_end_time("平均推力[N]")
    graph.bdf = logger.bdf
    print("Creating graphs...")
    graph.generate_general_graph("データ取得開始時","推力[N]")
    
    for colname in ml:
        graph.generate_general_graph("データ取得開始時",colname)
elif mode=="full":
    start = time.time()
    print("Analysing converted data...")
    logger.calcu_moving_ave("推力[N]","平均推力[N]")
    logger.calcu_moving_ave("圧力1[Pa]","平均圧力1[Pa]")
    logger.calcu_moving_ave("圧力2[Pa]","平均圧力2[Pa]")
    logger.calcu_moving_ave("圧力3[Pa]","平均圧力3[Pa]")
    logger.calcu_moving_ave("圧力4[Pa]","平均圧力4[Pa]")
   
    logger.calcu_burn_start_time("平均推力[N]")
    logger.calcu_thrust_ess()
    logger.correct_thurst("補正推力[N]")
    logger.calcu_operation_end_time("補正推力[N]")
    logger.create_burndata()
    logger.calcu_burn_end_time("平均推力[N]")
    analyzing_tiime = time.time() - start

    exportcsv = logger.bdf
    exportcsv = exportcsv[exportcsv["データ取得開始時"]>0]
    exportcsv.to_csv(os.path.join(aboutdir,"burntime3.csv"))
    print("----------")
    print("定常偏差",round(logger.ess,1),"N")
    print("燃焼終了時間",logger.burn_end_time,"s")
    print("作動終了時間",(logger.operation_end_time - logger.burn_start_time)/1000000,"s")
    total,op = logger.calcu_totalimpulse("補正推力[N]")
    print("トータルインパルス",round(total,1),"N・s")
    print("作動時間トータルインパルス",round(op,1),"N・s")
    print("----------")

    graph = graph_generator(aboutdir, logger.bdf, "データ取得開始時")
    print("Creating graphs...")
    start = time.time()
    graph.generate_graph_from_series(logger.df["データ取得開始時"][::10000],logger.df["推力[N]"][::10000],"全体推力[N]")
    graph.generate_general_graph(["推力[N]","補正推力[N]","平均推力[N]","偏差標準偏差[N]"],"推力関連.png")
    graph.generate_general_graph(["圧力1[Pa]","圧力2[Pa]","圧力3[Pa]","圧力4[Pa]"],"圧力.png")
    graph.generate_general_graph(["低域温度1[℃]","低域温度2[℃]","低域温度3[℃]","高域温度1[℃]","高域温度2[℃]"],"温度.png")
    generate_graph_time = time.time() - start

    operationendrelative = (logger.operation_end_time - logger.burn_start_time)/1000000
    graph.generate_overview_graph("データ取得開始時","推力[N]",["圧力1[Pa]"],logger.burn_end_time,operationendrelative,logger.operating_totalimpulse, logger.burn_totalimpulse,date)
    graph.generate_overview_graph("データ取得開始時","平均推力[N]",["平均圧力1[Pa]"],logger.burn_end_time,operationendrelative,logger.operating_totalimpulse,logger.burn_totalimpulse,date)
    graph.generate_overview_graph("データ取得開始時","補正推力[N]",None,logger.burn_end_time,operationendrelative,logger.operating_totalimpulse,logger.burn_totalimpulse,date)

    print("raw解析時間: {}s\nデータ分析時間: {}s \nグラフ生成時間: {}s".format(rawconvert_time, analyzing_tiime, generate_graph_time))
elif mode=="manual":
    print("Manual mode generationg graph...")
    ccsv = pandas.read_csv(abredatafile)
    if(starttime is not None):
        ccsv=ccsv[(ccsv["データ取得開始時"]>=starttime)]
    if(endtime is not None):
        ccsv=ccsv[(ccsv["データ取得開始時"]<=endtime)]
    graph = graph_generator(aboutdir, ccsv, "データ取得開始時")
    simple_list= ["推力[N]","圧力1[Pa]","圧力2[Pa]","圧力3[Pa]","圧力4[Pa]","低域温度1[℃]","低域温度2[℃]","低域温度3[℃]","高域温度1[℃]","高域温度2[℃]"]
    for colname in simple_list:
        graph.generate_general_graph([colname], colname)