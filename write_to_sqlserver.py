import pandas as pd
import pyodbc
import uuid
from datetime import datetime

def get_last_row_from_excel(file_path):
    df = pd.read_excel(file_path)
    if df.empty:
        raise ValueError(f"{file_path} 没有数据")
    return df.iloc[-1]

def main():
    # 读取端口流量统计表
    port_file = '端口流量统计表.xlsx'
    port_row = get_last_row_from_excel(port_file)
    # 计算网络使用流量（MB）
    def parse_size(s):
        if isinstance(s, str):
            parts = s.strip().split()
            if len(parts) == 2:
                num, unit = parts
                num = float(num)
                unit = unit.upper()
                factor = {'B':1/1024/1024, 'KB':1/1024, 'MB':1, 'GB':1024, 'TB':1024*1024}
                for k in factor:
                    if unit.startswith(k):
                        return num * factor[k]
            elif len(parts) == 1 and parts[0].replace('.', '', 1).isdigit():
                return float(parts[0])
        elif isinstance(s, (int, float)):
            return float(s)
        return 0.0
    in_diff = parse_size(port_row['portInOctets_diff']) if 'portInOctets_diff' in port_row else 0
    out_diff = parse_size(port_row['portOutOctets_diff']) if 'portOutOctets_diff' in port_row else 0
    WLSYLL = in_diff + out_diff
    # 速率字段处理，转换为MB/s数值
    def parse_speed_mb(speed):
        if isinstance(speed, str):
            parts = speed.strip().split()
            if len(parts) == 2:
                num, unit = parts
                num = float(num)
                unit = unit.upper()
                if unit.startswith('KB'):
                    return round(num / 1024, 3)  # KB/s -> MB/s
                elif unit.startswith('MB'):
                    return round(num, 3)         # MB/s -> MB/s
                elif unit.startswith('GB'):
                    return round(num * 1024, 3)  # GB/s -> MB/s
                elif unit.startswith('B'):
                    return round(num / 1024 / 1024, 3)  # B/s -> MB/s
            elif len(parts) == 1 and parts[0].replace('.', '', 1).isdigit():
                return float(parts[0])
        elif isinstance(speed, (int, float)):
            return float(speed)
        return 0.0
    WLDKSYXXSL = parse_speed_mb(port_row.get('portInSpeed', ''))
    WLDKSYSXSL = parse_speed_mb(port_row.get('portOutSpeed', ''))
    # 记录时间
    collect_time = port_row.get('collect_time', '')
    if collect_time:
        # 兼容多种日期格式
        dt = pd.to_datetime(collect_time)
        JLRQ = dt.strftime('%Y%m%d')
        SJCJSJ = dt.strftime('%Y%m%d %H%M%S')
    else:
        now = datetime.now()
        JLRQ = now.strftime('%Y%m%d')
        SJCJSJ = now.strftime('%Y%m%d %H%M%S')
    # 读取风险数
    risk_file = 'sxwaf_risk_count_history.xlsx'
    risk_row = get_last_row_from_excel(risk_file)
    WLGJSBCS = int(risk_row['业务风险数分析']) if '业务风险数分析' in risk_row else 0
    # 自动截断字符串字段，防止超长
    def truncate(val, maxlen):
        return str(val)[:maxlen]
    # 查询online_detail表，统计login_time为JLRQ的记录数
    online_detail_count = 0
    try:
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=172.17.12.251;'
            'DATABASE=SAMDB;'
            'UID=sa;PWD=ruijie@2023'
        )
        cursor2 = conn.cursor()
        sql_count = f"SELECT COUNT(*) FROM ONLINE_DETAIL WHERE CONVERT(date, LOGIN_TIME) = ?"
        cursor2.execute(sql_count, (dt.strftime('%Y-%m-%d'),))
        online_detail_count = cursor2.fetchone()[0]
        cursor2.close()
    except Exception as e:
        online_detail_count = 0
    # 组装数据
    row = {
        'ZJSJWYXBS': truncate(uuid.uuid4().hex, 32),
        'XXDM': truncate('1234567890', 20),
        'WLSYJLS': int(online_detail_count),
        'WLSYLL': float(WLSYLL),
        'WLGJSBCS': int(WLGJSBCS),
        'WLDKSYSXSL': WLDKSYSXSL,
        'WLDKSYXXSL': WLDKSYXXSL,
        'JLRQ': truncate(JLRQ, 20),
        'SJCJSJ': truncate(SJCJSJ, 20)
    }
    # 连接SQL Server
    conn_str = (
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=172.17.12.251;'
        'DATABASE=SAMDB;'
        'UID=sa;PWD=ruijie@2023'
    )
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    sql = '''
    INSERT INTO dbo.ods_wlaqglsj
    (ZJSJWYXBS, XXDM, WLSYJLS, WLSYLL, WLGJSBCS, WLDKSYSXSL, WLDKSYXXSL, JLRQ, SJCJSJ)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    cursor.execute(sql, row['ZJSJWYXBS'], row['XXDM'], row['WLSYJLS'], row['WLSYLL'], row['WLGJSBCS'], row['WLDKSYSXSL'], row['WLDKSYXXSL'], row['JLRQ'], row['SJCJSJ'])
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == '__main__':
    main() 