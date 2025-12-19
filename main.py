import analysis as ana
from dataanlysis import Logger
from graphgenerator import graph_generator
# from graphgenerator import graphgenerator as gg
import os

maindir = "2025-12-06-01"
rawfile ="LOG-0000001.csv"
redatafile = "converted.csv"
outdir = "outnew"
mode="full" #full or fast
run_analysis = True #解析ファイルが存在するときはFalse

abrawfile = os.path.join(maindir,rawfile)
abredatafile = os.path.join(maindir,redatafile)
aboutdir = os.path.join(maindir,outdir)

#未実装
date = None


#出力フォルダがなかったら作る
os.makedirs(aboutdir, exist_ok=True)
#解析
if run_analysis:
    print("Analysing raw data...")
    ana.data2graph(abrawfile,abredatafile,500)

logger = Logger(abredatafile, aboutdir,"データ取得開始時","推力[N]")
graph = graph_generator(aboutdir)

ml = ["推力[N]","補正推力[N]","平均推力[N]","圧力1[Pa]","圧力2[Pa]","圧力3[Pa]","圧力4[Pa]","低域温度1[℃]","低域温度2[℃]","低域温度3[℃]","高域温度1[℃]","高域温度2[℃]"]

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
  
    print("定常偏差",logger.ess)
    print("burnend",logger.burn_end_time)
    print("operationend",(logger.operation_end_time - logger.burn_start_time)/1000000)
    total,op = logger.calcu_totalimpulse("補正推力[N]")
    print("total_impulse",total,"N・s")
    print("operating_totalimpulse",op,"N・s")

    graph.bdf = logger.bdf
    print("Creating graphs...")
    graph.generate_general_graph("データ取得開始時","推力[N]")
    for colname in ml:
        graph.generate_general_graph("データ取得開始時",colname)

    graph.generate_overview_graph("データ取得開始時","平均推力[N]","平均圧力1[Pa]","平均圧力4[Pa]",logger.burn_end_time,logger.operating_totalimpulse,logger.burn_totalimpulse)
