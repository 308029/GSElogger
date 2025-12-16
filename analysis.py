import csv
import sys
import math

voltageref5v = 4.99
amp_gain = 47.0

def data2graph(source,target,loadcell_max_lbf=1000):
    with open(source) as fr:
        reader = csv.reader(fr)
        with open(target, 'w', encoding='utf_8_sig',newline="") as fw:
             writer = csv.writer(fw)
             writer.writerow(['書き込み待ちデータ数','データ取得開始時','データ取得終了時','推力[N]','圧力1[Pa]','圧力2[Pa]','圧力3[Pa]','圧力4[Pa]','低域温度1','低域温度2','低域温度3','高域温度1','高域温度2'])
             for row in reader:
                # 1行ずつ読み込み
                writer.writerow([row[0],row[1],row[2],str(bin2Thrust(int(row[3]),loadcell_max_lbf)),str(bin2dataPressure(int(row[5]))),str(bin2dataPressure(int(row[6]))),str(bin2dataPressure(int(row[7]))),str(bin2dataPressure(int(row[8]))),str(bin2dataTempLow(int(row[11]))),str(bin2dataTempLow(int(row[12]))),str(bin2dataTempLow2(int(row[13]))),str(bin2dataTempHigh(int(row[14]))),str(bin2dataTempHigh(int(row[15]))),row[19]])
                
#各列のデータ内容はcontent.csvを参照
def bin2ADCvoltage(binary):
    return voltageref5v * float(binary) / 4095#12bit-1

'''
理論値
250lbf = 1112.06 N について，5.1* 20 * 1e-3 V の出力が得られる
'''
def bin2ThrustIdeal(binary):
    sensorOutputVoltage = bin2ADCvoltage(binary)/amp_gain
    return 1112.06 * sensorOutputVoltage / (voltageref5v * 20.0 * 1e-3) # N

'''
実験値
ADCの値 x に対して，力 y[N] は，y = 0.5952 * x - 20.177
'''
def bin2Thrust(binary,loadcell_max_lbf):
    if loadcell_max_lbf == 250:
        return bin2Thrust250(binary)
    elif loadcell_max_lbf == 500:
        return bin2Thrust500(binary)
    elif loadcell_max_lbf == 1000:
        return bin2Thrust1000(binary)
    else:
        print("Unsupported loadcell max lbf:",loadcell_max_lbf)
        return 0
def bin2Thrust250(binary):
    return 0.5807 * binary - 24.098
def bin2Thrust1000(binary): #コンクリブロック法でやった時の校正値
    return 2.3896*binary-115.47
def bin2Thrust500(binary): #コンクリブロック法（2025/12/03実施）
    return 1.2836*binary-49.93

def bin2dataPressure(binary):
    sensorOutputVoltage = 2.0 * bin2ADCvoltage(binary)
    return sensorOutputVoltage * 1e6 # Nm^-2

def bin2dataTempHigh(binary):
    R = 10000
    return bin2dataTemp(binary,R)

def bin2dataTempLow(binary):
    R = 100
    return bin2dataTemp(binary,R)

def bin2dataTempLow2(binary):
    R=100
    return bin2dataTempNew(binary,R)

def bin2dataTemp(binary,R):
    # サーミスタの抵抗値を計算
    v = bin2ADCvoltage(binary)
    R_T = R * v / (voltageref5v -v)

    if R_T == 0:
        return 0

    # サーミスタの抵抗値から温度を計算
    B = 3435 # B係数
    R0 = 10000
    T0 = 25 + 273.15

    T = 1/(1/B * math.log(R_T/R0)+ 1/T0)
    T -= 273.15
    return T
def bin2dataTempNew(binary,R):
    # サーミスタの抵抗値を計算
    v = bin2ADCvoltage(binary)
    R_T = R * v / (voltageref5v -v)

    if R_T == 0:
        return 0

    # サーミスタの抵抗値から温度を計算
    B = 4126 # B係数
    R0 = 10000
    T0 = 25 + 273.15

    T = 1/(1/B * math.log(R_T/R0)+ 1/T0)
    T -= 273.15
    return T

'''
def bin2dataTemp(binary,R):
    if(binary == 0):
        return -273
    Voltage = bin2ADCvoltage(binary)
    return 1/(1/(25+273)+math.log(((Voltage/(5.1-Voltage))*R)/10000)/4126)-273
'''

if __name__ == "__main__":
    #    args = sys.argv
    inputfilepath = "2025-12-06-02.csv" 
    outputfilepath = "converted.csv"
    data2graph(inputfilepath,outputfilepath)