import math

# --- 定数定義 ---
VOLTAGE_REF_5V = 4.99

R0 = 10000
T0 = 25 + 273.15  # 298.15
Tempnew_B = 4126
Temp_B = 3435

HighTemp_R = 10000
LowTemp_R = 1000

def adc_voltage(adc_val):
    """ADC値を電圧[V]に変換する

    Args:
        adc_val (float or int): ADCのバイナリ値 (0 - 4095)
    Returns:
        float: 電圧 [V]
    """
    return (VOLTAGE_REF_5V * float(adc_val)) / 4095.0

def thrust(adc_val, max_lbf):
    """ADC値から推力[N]を計算する

    Args:
        adc_val (float or int): ADC値
        max_lbf (int): ロードセルの最大定格 (250, 500, 1000)
    Returns:
        float: 推力 [N]
    """
    val = float(adc_val)
    if max_lbf == 250:
        return 0.5807 * val - 24.098
    elif max_lbf == 500:
        return 1.2836 * val - 49.93
    else:  # 1000
        return 2.3896 * val - 115.47

def pressure(adc_val):
    """ADC値から圧力[Pa]を計算する

    Args:
        adc_val (float or int): ADC値
    Returns:
        float: 圧力 [Pa]
    """
    v = adc_voltage(adc_val)
    return 2.0 * v * 1e6

def temp(adc_val, R, B):
    """ADC値からサーミスタ温度[℃]を計算する

    Args:
        adc_val (float or int): ADC値
        R (float): 基準抵抗値 (HighTemp_R または LowTemp_R)
        B (float): B定数 (Temp_B または Tempnew_B)
    Returns:
        float: 温度 [℃]
    """
    v = adc_voltage(adc_val)
    
    # ゼロ除算および対数エラーの回避
    if v >= VOLTAGE_REF_5V:
        v = VOLTAGE_REF_5V - 1e-6
    elif v <= 0:
        v = 1e-6
        
    rt = R * v / (VOLTAGE_REF_5V - v)
    
    if rt <= 0:
        rt = 1e-6

    # サーミスタ計算式: T = 1 / (1/B * ln(Rt/R0) + 1/T0) - 273.15
    t_kelvin = 1.0 / ((1.0 / B) * math.log(rt / R0) + (1.0 / T0))
    return t_kelvin - 273.15

# --- 特定のセンサ用のショートカット関数 ---

def temp_low(adc_val):
    """低域温度 (通常) [℃] を計算する"""
    return temp(adc_val, LowTemp_R, Temp_B)

def temp_low_new(adc_val):
    """低域温度 (新) [℃] を計算する"""
    return temp(adc_val, LowTemp_R, Tempnew_B)

def temp_high(adc_val):
    """高域温度 [℃] を計算する"""
    return temp(adc_val, HighTemp_R, Temp_B)
