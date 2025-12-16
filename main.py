import analysis as han
import graph as graph
import os

maindir = "2025-12-06-02"
rawfile ="LOG-0000001.csv"
redatafile = "converted.csv"
outdir = "out"

abrawfile = os.path.join(maindir,rawfile)
abredatafile = os.path.join(maindir,redatafile)
aboutdir = os.path.join(maindir,outdir)

#出力フォルダがなかったら作る
os.makedirs(aboutdir, exist_ok=True)
#解析
han.main(abrawfile,abredatafile)
graph.data2graph(abredatafile, aboutdir)