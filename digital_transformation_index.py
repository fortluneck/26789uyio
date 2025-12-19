import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import os
import platform
import subprocess
from datetime import datetime

# ==============================================
# 数字化转型指数计算主程序（新手友好版）
# ==============================================

# ----------------------
# 1. 读取数据文件
# ----------------------
print('正在读取2013年年报词频统计数据...')
file_path = '2013年年报技术关键词统计.xlsx'

try:
    df = pd.read_excel(file_path)
    print(f'成功读取文件: {file_path}')
    # 确保股票代码为6位数格式
    if '股票代码' in df.columns:
        # 对非'未知'的股票代码进行处理，确保为6位数格式
        df['股票代码'] = df['股票代码'].apply(lambda x: str(x).zfill(6) if isinstance(x, (str, int)) and str(x) != '未知' and len(str(x)) < 6 else x)
except Exception as e:
    print(f'错误：无法读取文件: {str(e)}')
    input('按回车键退出...')
    exit()

if df is None:
    print('错误：无法读取文件，请检查文件是否存在')
    input('按回车键退出...')
    exit()

# ----------------------
# 2. 数据清洗与验证
# ----------------------
print('正在验证数据格式...')
required_columns = ['股票代码', '企业名称']
missing_columns = [col for col in required_columns if col not in df.columns]

if missing_columns:
    print(f'错误：数据缺少必要的列: {missing_columns}')
    input('按回车键退出...')
    exit()

# 检查技术关键词列是否存在
tech_columns = ['人工智能词频数', '大数据词频数', '云计算词频数', '区块链词频数', '数字技术运用词频数']
missing_tech_cols = [col for col in tech_columns if col not in df.columns]
if missing_tech_cols:
    print(f'警告：缺少以下技术关键词列: {missing_tech_cols}，将忽略这些指标')

initial_count = len(df)
# 只删除技术关键词列中有缺失值的行
tech_columns = [col for col in tech_columns if col in df.columns]
df_cleaned = df.dropna(subset=tech_columns + required_columns)
deleted_count = initial_count - len(df_cleaned)
print(f'数据清洗完成：共 {initial_count} 条记录，删除 {deleted_count} 条不完整记录')

# ----------------------
# 3. 数据标准化与PCA分析
# ----------------------
# 排除非技术列（股票代码、企业名称、年份）
required_columns = ['股票代码', '企业名称']
exclude_columns = required_columns + ['年份']
technical_columns = [col for col in df.columns if col not in exclude_columns]

print(f'将用于计算的技术指标: {technical_columns}')
X = df_cleaned[technical_columns].values

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

pca = PCA()
pca.fit(X_scaled)
cumulative_variance = np.cumsum(pca.explained_variance_ratio_)
n_components = np.argmax(cumulative_variance >= 0.85) + 1
print(f'选择 {n_components} 个主成分，累计解释方差比例: {cumulative_variance[n_components-1]:.2%}')

pca = PCA(n_components=n_components)
principal_components = pca.fit_transform(X_scaled)
weights = np.sum(np.abs(pca.components_), axis=0)
weights = weights / np.sum(weights)

# ----------------------
# 4. 指数计算
# ----------------------
index_values = np.dot(X_scaled, weights)
normalized_index = ((index_values - index_values.min()) / (index_values.max() - index_values.min()) * 100).round().astype(int)

result_df = df_cleaned[required_columns + ['年份']].copy()
result_df['数字化转型指数(0-100分)'] = normalized_index

# 添加原始词频数据和总词频数
for col in technical_columns:
    result_df[col] = df_cleaned[col]
result_df['总词频数'] = df_cleaned[technical_columns].sum(axis=1)

# ----------------------
# 5. 保存结果（含错误处理）
# ----------------------
print('正在保存结果文件...')

def get_unique_filename(base_name):
    """生成唯一文件名，避免覆盖和权限问题"""
    if not os.path.exists(base_name):
        return base_name
    # 添加时间戳确保唯一性
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name, ext = os.path.splitext(base_name)
    return f"{name}_{timestamp}{ext}"

try:
    # 尝试保存文件，如遇权限问题则生成唯一文件名
    output_file = get_unique_filename('2013年数字化转型指数结果表.xlsx')
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df_cleaned.to_excel(writer, sheet_name='1_原始数据', index=False)
        pd.DataFrame(X_scaled, columns=technical_columns).to_excel(writer, sheet_name='2_标准化数据', index=False)
        pd.DataFrame({'指标名称': technical_columns, '权重值': weights}).to_excel(writer, sheet_name='3_主成分权重', index=False)
        result_df.to_excel(writer, sheet_name='4_指数结果', index=False)
    
    print(f'结果已成功保存至: {os.path.abspath(output_file)}')
    
    # 尝试自动打开文件
    try:
        if platform.system() == 'Windows':
            os.startfile(output_file)
        else:
            subprocess.run(['open' if platform.system() == 'Darwin' else 'xdg-open', output_file])
        print('结果文件已自动打开')
    except Exception as e:
        print(f'自动打开文件失败，请手动打开: {output_file}')

except PermissionError:
    print("\n错误：无法写入文件，可能原因及解决方法：")
    print("1. 请确保Excel文件没有被打开")
    print("2. 尝试以管理员身份运行此程序")
    print("3. 将文件保存到其他位置（如桌面）")
    output_file = os.path.expanduser(f'~/Desktop/2013年数字化转型指数结果表.xlsx')
    print(f'已尝试保存到桌面: {output_file}')
except Exception as e:
    print(f'保存文件时发生错误: {str(e)}')

# 在非交互式环境中自动退出
import sys
try:
    # 尝试使用input函数（交互式环境）
    input('处理完成，按回车键关闭窗口...')
except EOFError:
    # 在非交互式环境中直接退出
    print('处理完成，程序已自动退出')
    sys.exit(0)