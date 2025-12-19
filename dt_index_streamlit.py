import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import plotly.express as px

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 设置页面配置
st.set_page_config(
    page_title="数字化转型指数分析",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 数据加载与处理
@st.cache_data
def load_data():
    """加载并处理数字化转型指数数据"""
    file_path = r"生成app资料\1999-2023年数字化转型指数与行业合并表.xlsx"
    try:
        df = pd.read_excel(file_path)
        
        # 数据处理
        df['股票代码'] = df['股票代码'].apply(lambda x: str(x).zfill(6) if isinstance(x, (str, int)) and str(x) != '未知' and len(str(x)) < 6 else x)
        # 确保股票代码全部为字符串类型
        df['股票代码'] = df['股票代码'].astype(str)
        df = df.dropna(subset=['股票代码', '企业名称', '数字化转型指数(0-100分)'])
        
        # 确保年份为整数
        df['年份'] = df['年份'].astype(int)
        
        return df
    except Exception as e:
        st.error(f"数据加载失败: {str(e)}")
        return None

# 加载数据
df = load_data()

if df is not None:
    # 应用标题
    st.title("数字化转型指数分析平台")
    st.markdown("---")
    
    # 侧边栏筛选器
    st.sidebar.header("数据筛选")
    
    # 年份筛选
    years = sorted(df['年份'].unique())
    selected_year = st.sidebar.selectbox("选择年份", years, index=len(years)-1)
    
    # 行业筛选（处理NaN值）
    # 将NaN值替换为'未知行业'
    df['行业名称'] = df['行业名称'].fillna('未知行业')
    industries = sorted(df['行业名称'].unique())
    selected_industry = st.sidebar.selectbox("选择行业", ['全部'] + industries)
    
    # 指数范围筛选
    min_index = int(df['数字化转型指数(0-100分)'].min())
    max_index = int(df['数字化转型指数(0-100分)'].max())
    index_range = st.sidebar.slider(
        "数字化转型指数范围",
        min_value=min_index,
        max_value=max_index,
        value=(min_index, max_index)
    )
    
    # 企业查询
    company_search = st.sidebar.text_input("搜索企业名称或股票代码")
    
    # 数据筛选逻辑
    filtered_df = df.copy()
    filtered_df = filtered_df[filtered_df['年份'] == selected_year]
    
    if selected_industry != '全部':
        filtered_df = filtered_df[filtered_df['行业名称'] == selected_industry]
    
    filtered_df = filtered_df[
        (filtered_df['数字化转型指数(0-100分)'] >= index_range[0]) &
        (filtered_df['数字化转型指数(0-100分)'] <= index_range[1])
    ]
    
    if company_search:
        filtered_df = filtered_df[
            filtered_df['企业名称'].str.contains(company_search, case=False) |
            filtered_df['股票代码'].str.contains(company_search, case=False)
        ]
    
    # 主内容区域
    main_content = st.container()
    
    with main_content:
        # 数据概览
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("企业数量", filtered_df.shape[0])
        
        # 处理空数据情况
        if filtered_df.empty:
            # 隐藏空的指标卡片
            with col2:
                st.empty()
            with col3:
                st.empty()
            with col4:
                st.empty()
            
            # 美化空数据提示
            st.markdown("---")
            st.subheader("🔍 没有找到匹配的数据")
            st.markdown("\n")
            
            col_guide1, col_guide2 = st.columns(2)
            
            with col_guide1:
                st.markdown("**建议尝试以下操作：**")
                st.markdown("- 调整年份选择")
                st.markdown("- 选择其他行业")
                st.markdown("- 扩大指数范围")
            
            with col_guide2:
                st.markdown("**热门行业推荐：**")
                # 获取所有年份中企业数量最多的3个行业
                top_industries = df.groupby('行业名称')['企业名称'].count().sort_values(ascending=False).head(3).index.tolist()
                for industry in top_industries:
                    st.markdown(f"- {industry}")
            
            st.markdown("\n")
            st.info("请调整左侧筛选条件以查看数据")
        else:
            avg_index = filtered_df['数字化转型指数(0-100分)'].mean()
            max_index = filtered_df['数字化转型指数(0-100分)'].max()
            min_index = filtered_df['数字化转型指数(0-100分)'].min()
            
            with col2:
                st.metric("平均指数", f"{avg_index:.1f}" if not pd.isna(avg_index) else "N/A")
            with col3:
                st.metric("最高指数", int(max_index) if not pd.isna(max_index) else 0)
            with col4:
                st.metric("最低指数", int(min_index) if not pd.isna(min_index) else 0)
        
        st.markdown("---")
        
        # 指数分布直方图
        st.subheader("数字化转型指数分布")
        if not filtered_df.empty:
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.histplot(
                filtered_df['数字化转型指数(0-100分)'],
                bins=20,
                kde=True,
                ax=ax,
                color='skyblue'
            )
            ax.set_title(f"{selected_year}年数字化转型指数分布")
            ax.set_xlabel("数字化转型指数")
            ax.set_ylabel("企业数量")
            st.pyplot(fig)
        else:
            st.info("暂无数据绘制直方图")
        
        # 技术维度分析（雷达图）
        st.subheader("技术维度分析")
        tech_dimensions = ['人工智能', '大数据', '云计算', '物联网', '区块链', '数字技术基础设施', '数字化应用场景']
        
        if not filtered_df.empty:
            # 计算平均技术指标
            tech_avg = filtered_df[tech_dimensions].mean().reset_index()
            tech_avg.columns = ['技术维度', '平均词频数']
            
            # 创建雷达图
            fig = px.line_polar(
                tech_avg, 
                r='平均词频数', 
                theta='技术维度', 
                line_close=True,
                title=f"{selected_year}年{selected_industry if selected_industry != '全部' else ''}平均技术维度分布"
            )
            st.plotly_chart(fig, width='stretch')
        
        # 企业排名表格
        st.subheader("企业排名")
        ranked_df = filtered_df.sort_values(by='数字化转型指数(0-100分)', ascending=False)
        
        # 显示前20名企业
        display_df = ranked_df[
            ['股票代码', '企业名称', '行业名称', '数字化转型指数(0-100分)', '总词频数']
        ].head(20)
        
        # 添加排名列
        display_df.insert(0, '排名', range(1, len(display_df) + 1))
        
        st.dataframe(display_df, width='stretch')
        
        # 行业对比分析
        st.subheader("行业对比分析")
        industry_comparison = df[df['年份'] == selected_year]
        industry_avg = industry_comparison.groupby('行业名称')['数字化转型指数(0-100分)'].mean().sort_values(ascending=False).reset_index()
        
        fig = px.bar(
            industry_avg.head(10),
            x='行业名称',
            y='数字化转型指数(0-100分)',
            title=f"{selected_year}年各行业平均数字化转型指数Top10",
            color='数字化转型指数(0-100分)',
            color_continuous_scale='Blues'
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, width='stretch')
        
        # 指数趋势分析
        st.subheader("数字化转型指数趋势")
        
        # 选择特定企业进行趋势分析
        if company_search:
            trend_df = df[
                (df['企业名称'].str.contains(company_search, case=False) |
                 df['股票代码'].str.contains(company_search, case=False))
            ].sort_values(by='年份')
            
            if not trend_df.empty:
                company_name = trend_df['企业名称'].iloc[0]
                fig = px.line(
                    trend_df,
                    x='年份',
                    y='数字化转型指数(0-100分)',
                    title=f"{company_name}数字化转型指数趋势",
                    markers=True
                )
                st.plotly_chart(fig, width='stretch')
            else:
                st.info("未找到匹配的企业数据")
else:
    st.error("请确保数据文件存在且格式正确")
    st.stop()
