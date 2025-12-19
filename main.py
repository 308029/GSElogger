import analysis as han
from dataanlysis import Logger
from graphgenerator import graph_generator
# from graphgenerator import graphgenerator as gg
import os

maindir = "2025-8-31"
rawfile ="LOG-0000001.csv"
redatafile = "converted.csv"
outdir = "out"
mode="fast" #full or fast

abrawfile = os.path.join(maindir,rawfile)
abredatafile = os.path.join(maindir,redatafile)
aboutdir = os.path.join(maindir,outdir)

#出力フォルダがなかったら作る
os.makedirs(aboutdir, exist_ok=True)
#解析
# han.main(abrawfile,abredatafile)

logger = Logger(abredatafile, aboutdir)
graph = graph_generator(aboutdir)

if mode=="fast":
    logger.calcu_moving_ave("推力[N]","平均推力[N]")
    logger.calcu_moving_ave("圧力1[Pa]","平均圧力1[Pa]")
    logger.calcu_moving_ave("圧力4[Pa]","平均圧力4[Pa]")
   
    print(logger.calcu_burn_start_time("データ取得開始時","平均推力[N]"))
    print(logger.calcu_thrust_ess("データ取得開始時","推力[N]"))
    logger.correct_thurst("補正推力[N]","推力[N]")
    logger.calcu_operation_end_time("データ取得開始時","補正推力[N]")
    logger.create_burndata("データ取得開始時","推力[N]")
    logger.calcu_burn_end_time("データ取得開始時","推力[N]","平均推力[N]")
  
    print(logger.ess)
    print("burnend",logger.burn_end_time)
    print("operationend",(logger.operation_end_time - logger.burn_start_time)/1000000)
    print("total,operating",logger.calcu_totalimpulse("データ取得開始時","補正推力[N]"))

    graph.bdf = logger.bdf

    graph.generate_general_graph("データ取得開始時","推力[N]")
    ml = ["推力[N]","補正推力[N]","平均推力[N]","偏差標準偏差[N]","圧力1[Pa]","圧力2[Pa]","圧力3[Pa]","圧力4[Pa]","低域温度1","低域温度2","低域温度3","高域温度1","高域温度2"]
    for colname in ml:
        graph.generate_general_graph("データ取得開始時",colname)

    graph.generate_overview_graph("データ取得開始時","平均推力[N]","平均圧力1[Pa]","平均圧力4[Pa]",logger.burn_end_time,logger.operating_totalimpulse,logger.burn_totalimpulse)
elif mode=="full":
    logger.df["平均推力[N]"] = logger.calcu_moving_ave("推力[N]")
    logger.burn_start_time = logger.calcu_burn_start_time(logger.df)
    logger.ess = logger.calcu_ess()
    logger.burn_end_time = logger.calcu_burn_end_time()
    burntotalimpulse,operationgtotalimpulse = logger.calcu_totalimpulse()
    logger.create_thrust_graph()
    logger.create_overview_graph()
    for colname in ml:
        logger.create_general_graph()
