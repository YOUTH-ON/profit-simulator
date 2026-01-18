import streamlit as st
import pandas as pd
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

# ページ設定
st.set_page_config(page_title="5ヵ年財務シミュレーター", layout="wide")

st.title("🏦 5ヵ年詳細財務シミュレーター")
st.caption("中小法人税率対応・減価償却逓減モデル / 単位：千円")

# --- 基準値入力 ---
st.subheader("📌 シミュレーション基準値")
with st.container(border=True):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        start_month = st.date_input("試算開始月", value=date.today().replace(day=1))
        init_cash = st.number_input("期首現預金残高", value=10000)
    with c2:
        gp_rate_val = st.number_input("売上総利益率 (%)", value=10.0) / 100
        op_rate_val = st.number_input("営業利益率 (%)", value=3.0) / 100
        ord_rate_val = st.number_input("経常利益率 (%)", value=3.0) / 100
    with c3:
        init_debt = st.number_input("期首借入金残高", value=50000)
        monthly_repayment = st.number_input("借入金返済額 (月額)", value=500)
    with c4:
        init_depr_annual = st.number_input("減価償却費 (1年目年額)", value=6000)
        depr_decay_rate = 0.90 # 減少率90%

st.divider()

# --- 案件別売上明細 ---
st.subheader("📝 案件別売上明細")
default_projects = pd.DataFrame([
    {"案件名": "案件A", "月額売上(千円)": 10000, "入金サイト(ヶ月)": 1},
])
df_projects = st.data_editor(default_projects, num_rows="dynamic", use_container_width=True)

# --- 計算ロジック ---
months = 60
sim_data = []
current_debt = init_debt
current_cash = init_cash
collection_schedule = {}

for m in range(months):
    target_date = start_month + relativedelta(months=m)
    year_idx = m // 12
    
    # 1. 減価償却費の計算 (年ごとに90%に減少)
    current_annual_depr = init_depr_annual * (depr_decay_rate ** year_idx)
    monthly_depr = current_annual_depr / 12
    
    # 2. 損益計算 (発生ベース)
    revenue = df_projects["月額売上(千円)"].sum()
    gross_profit = revenue * gp_rate_val
    cost_of_sales = revenue - gross_profit
    op_profit = revenue * op_rate_val
    sga_expenses = gross_profit - op_profit
    ord_profit = revenue * ord_rate_val
    
    # 3. 法人税計算 (所得800万以下15%, 超過23.2%の簡易モデル)
    # 月次に直して計算
    tax_base = max(0, ord_profit)
    threshold_monthly = 8000 / 12
    if tax_base <= threshold_monthly:
        tax = tax_base * 0.15
    else:
        tax = (threshold_monthly * 0.15) + ((tax_base - threshold_monthly) * 0.232)
    
    net_profit = ord_profit - tax
    
    # 4. キャッシュフロー計算
    # 入金登録
    for _, row in df_projects.iterrows():
        c_date = target_date + relativedelta(months=int(row["入金サイト(ヶ月)"]))
        collection_schedule[c_date] = collection_schedule.get(c_date, 0) + row["月額売上(千円)"]
    
    cash_in = collection_schedule.get(target_date, 0)
    simple_cf = net_profit + monthly_depr
    
    # 支出（売上 - 営業利益 - 償却費 = 実際の現金支出を伴う費用）
    actual_expenses_out = revenue - op_profit - monthly_depr
    
    # 返済
    actual_repayment = min(current_debt, simple_cf + monthly_repayment)
    current_debt -= actual_repayment
    
    # 現金残高更新
    current_cash = current_cash + cash_in - actual_expenses_out - tax - actual_repayment
    
    sim_data.append({
        "年度": f"{year_idx + 1}年目",
        "年月": target_date.strftime("%Y/%m"),
        "売上高": revenue,
        "売上原価": cost_of_sales,
        "売上総利益": gross_profit,
        "売上総利益率": gp_rate_val,
        "販管費": sga_expenses,
        "営業利益": op_profit,
        "営業利益率": op_rate_val,
        "経常利益": ord_profit,
        "経常利益率": ord_rate_val,
        "法人税等": tax,
        "当期純利益": net_profit,
        "減価償却費": monthly_depr,
        "簡易CF": simple_cf,
        "返済額": actual_repayment,
        "借入金残高": current_debt,
        "現預金残高": current_cash
    })

df_all = pd.DataFrame(sim_data)

# --- 表示用処理 ---
def format_df(df):
    return df.style.format({
        "売上高": "{:,.0f}", "売上原価": "{:,.0f}", "売上総利益": "{:,.0f}",
        "販管費": "{:,.0f}", "営業利益": "{:,.0f}", "経常利益": "{:,.0f}",
        "法人税等": "{:,.0f}", "当期純利益": "{:,.0f}", "減価償却費": "{:,.0f}",
        "簡易CF": "{:,.0f}", "返済額": "{:,.0f}", "借入金残高": "{:,.0f}",
        "現預金残高": "{:,.0f}", "売上総利益率": "{:.1%}", "営業利益率": "{:.1%}", "経常利益率": "{:.1%}"
    })

# --- 画面構成 ---
tab1, tab2 = st.tabs(["📅 月次シミュレーション", "📊 年次サマリー"])

with tab1:
    st.subheader("📋 損益試算表 (月次)")
    pl_cols = ["年月", "売上高", "売上原価", "売上総利益", "売上総利益率", "販管費", "営業利益", "営業利益率", "経常利益", "経常利益率", "法人税等", "当期純利益"]
    st.dataframe(format_df(df_all[pl_cols]), use_container_width=True)
    
    st.subheader("📋 簡易CF計算書 (月次)")
    cf_cols = ["年月", "当期純利益", "減価償却費", "簡易CF", "返済額", "借入金残高", "現預金残高"]
    st.dataframe(format_df(df_all[cf_cols]), use_container_width=True)

with tab2:
    # 年次集計
    df_yearly = df_all.groupby("年度").agg({
        "売上高": "sum", "売上原価": "sum", "売上総利益": "sum", "販管費": "sum",
        "営業利益": "sum", "経常利益": "sum", "法人税等": "sum", "当期純利益": "sum",
        "減価償却費": "sum", "簡易CF": "sum", "返済額": "sum",
        "借入金残高": "last", "現預金残高": "last"
    }).reset_index()
    # 比率の再計算
    df_yearly["売上総利益率"] = df_yearly["売上総利益"] / df_yearly["売上高"]
    df_yearly["営業利益率"] = df_yearly["営業利益"] / df_yearly["売上高"]
    df_yearly["経常利益率"] = df_yearly["経常利益"] / df_yearly["売上高"]

    st.subheader("📈 年次損益・CFサマリー")
    st.dataframe(format_df(df_yearly), use_container_width=True)
    
    # グラフ
    st.line_chart(df_yearly.set_index("年度")[["現預金残高", "借入金残高"]])

# ダウンロード
csv = df_all.to_csv(index=False).encode('utf-8-sig')
st.download_button("全データをCSVで保存", csv, "full_sim_result.csv", "text/csv")
