import streamlit as st
import pandas as pd
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

# ページ設定
st.set_page_config(page_title="高度資金繰り・損益シミュレーター", layout="wide")

st.title("🚀 高度資金繰り・損益シミュレーター (5ヵ年月次)")
st.caption("案件別入金サイト・月次CFシミュレーション対応版 / 単位：千円")

# --- ①②③④ 画面上部：基準値入力表 ---
st.subheader("📌 シミュレーション基準値")
with st.container(border=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        start_month = st.date_input("試算開始月", value=date.today().replace(day=1))
        init_cash = st.number_input("期首現預金残高 (千円)", value=10000)
    with col2:
        gp_rate_val = st.number_input("売上総利益率 (%)", value=40.0) / 100
        op_rate_val = st.number_input("営業利益率 (%)", value=10.0) / 100
    with col3:
        init_debt = st.number_input("期首借入金残高 (千円)", value=50000)
        monthly_repayment = st.number_input("借入金返済額 (月額/千円)", value=500)
    with col4:
        depreciation_annual = st.number_input("減価償却費 (年額/千円)", value=6000)
        depreciation_monthly = depreciation_annual / 12

st.divider()

# --- ⑤ 案件別売上明細入力 ---
st.subheader("📝 案件別売上明細")
st.info("案件名、月額売上、入金サイト（0=当月, 1=翌月...）を入力してください。")

# 初期データ
default_projects = pd.DataFrame([
    {"案件名": "既存顧客A", "月額売上(千円)": 5000, "入金サイト(ヶ月)": 1},
    {"案件名": "新規案件B", "月額売上(千円)": 2000, "入金サイト(ヶ月)": 2},
])

# データエディタで表形式入力（行の追加・削除可能）
df_projects = st.data_editor(
    default_projects,
    num_rows="dynamic",
    use_container_width=True,
    key="project_editor"
)

st.divider()

# --- ⑥⑦ 損益・資金繰り計算ロジック (60ヶ月) ---
months_to_simulate = 60
sim_dates = [start_month + relativedelta(months=i) for i in range(months_to_simulate)]

# 計算用バッファ
monthly_data = []
current_debt = init_debt
current_cash = init_cash

# 入金予定を保持する辞書 {日付: 入金額}
collection_schedule = {}

for d in sim_dates:
    # 1. 売上計算（発生ベース）
    total_revenue_accrual = df_projects["月額売上(千円)"].sum()
    
    # 2. 入金予定の登録（サイト考慮）
    for _, row in df_projects.iterrows():
        collection_date = d + relativedelta(months=int(row["入金サイト(ヶ月)"]))
        amt = row["月額売上(千円)"]
        collection_schedule[collection_date] = collection_schedule.get(collection_date, 0) + amt

    # 3. 当月の入金実行
    cash_in = collection_schedule.get(d, 0)
    
    # 4. 利益計算
    operating_profit = total_revenue_accrual * op_rate_val
    simple_cf = operating_profit + depreciation_monthly
    
    # 5. 借入金返済
    # 営業利益＋償却費(簡易CF)を返済原資とするルール + 約定返済
    repayment_power = simple_cf + monthly_repayment
    actual_repayment = min(current_debt, repayment_power)
    current_debt -= actual_repayment
    
    # 6. 現預金推移
    # 入金(CashIn) - 変動費・固定費相当 - 返済
    # 営業利益 = 売上 - 費用 なので、支出額 = 売上 - 営業利益
    outflow_except_repayment = total_revenue_accrual - operating_profit
    current_cash = current_cash + cash_in - (outflow_except_repayment - depreciation_monthly) - actual_repayment

    monthly_data.append({
        "年月": d.strftime("%Y/%m"),
        "売上(発生)": total_revenue_accrual,
        "入金(回収)": cash_in,
        "営業利益": operating_profit,
        "簡易CF": simple_cf,
        "返済額": actual_repayment,
        "借入金残高": current_debt,
        "現預金残高": current_cash
    })

df_result = pd.DataFrame(monthly_data)

# --- 結果の表示 ---
st.subheader("📈 シミュレーション結果")

# グラフ：借入金と現預金の推移
st.line_chart(df_result.set_index("年月")[["借入金残高", "現預金残高"]])

# 明細表
st.subheader("📊 月次明細表 (5ヵ年)")
st.dataframe(
    df_result.style.format({
        "売上(発生)": "{:,.0f}",
        "入金(回収)": "{:,.0f}",
        "営業利益": "{:,.1f}",
        "簡易CF": "{:,.1f}",
        "返済額": "{:,.0f}",
        "借入金残高": "{:,.0f}",
        "現預金残高": "{:,.0f}"
    }),
    use_container_width=True
)

# ダウンロード
csv = df_result.to_csv(index=False).encode('utf-8-sig')
st.download_button("CSVでエクスポート", csv, "sim_result.csv", "text/csv")
