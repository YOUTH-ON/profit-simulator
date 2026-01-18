import streamlit as st
import pandas as pd

# ページ設定
st.set_page_config(page_title="5ヵ年損益・資金推移シミュレーター", layout="wide")

st.title("📊 5ヵ年損益・資金推移シミュレーター")
st.caption("M4 MacBook Air 最適化版（高互換モード） / 単位：千円")

# --- サイドバー：入力パラメータ ---
st.sidebar.header("📈 入力設定（年額）")

rev_0 = st.sidebar.number_input("基準売上高 (千円)", value=100000, step=1000)
gp_rate = st.sidebar.slider("売上総利益率 (%)", 0, 100, 40) / 100
op_rate = st.sidebar.slider("営業利益率 (%)", 0, 100, 10) / 100
depreciation = st.sidebar.number_input("減価償却費 (千円)", value=5000, step=100)
init_cash = st.sidebar.number_input("期首現預金残高 (千円)", value=10000, step=1000)
init_debt = st.sidebar.number_input("期首借入金残高 (千円)", value=50000, step=1000)
debt_repayment = st.sidebar.number_input("年間借入金返済額 (千円)", value=5000, step=500)

# --- シミュレーションロジック ---
years = [0, 1, 2, 3, 4, 5]
data = []

current_debt = init_debt
current_cash = init_cash

for year in years:
    if year == 0:
        data.append({
            "年目": "0",
            "売上高": 0,
            "営業利益": 0,
            "簡易CF": 0,
            "借入金残高": current_debt,
            "現預金残高": current_cash
        })
    else:
        revenue = rev_0
        operating_profit = revenue * op_rate
        simple_cf = operating_profit + depreciation
        
        # 借入金返済
        total_repayment_capacity = simple_cf + debt_repayment
        repayment_actual = min(current_debt, total_repayment_capacity)
        current_debt -= repayment_actual
        
        # 現預金推移
        current_cash += (simple_cf - debt_repayment)

        data.append({
            "年目": str(year),
            "売上高": revenue,
            "営業利益": operating_profit,
            "簡易CF": simple_cf,
            "借入金残高": current_debt,
            "現預金残高": current_cash
        })

df_sim = pd.DataFrame(data)

# --- メイン画面表示 ---
col1, col2 = st.columns(2)
with col1:
    st.metric("5年後の借入金残高", f"¥{int(current_debt):,} 千円")
with col2:
    st.metric("5年後の現預金推計", f"¥{int(current_cash):,} 千円")

st.divider()

# --- グラフ表示（Streamlitネイティブグラフ） ---
st.subheader("財務推移の可視化")

# グラフ用のデータ整形
df_plot = df_sim.set_index("年目")

col_left, col_right = st.columns(2)
with col_left:
    st.write("▼ 借入金残高の推移")
    st.bar_chart(df_plot["借入金残高"])

with col_right:
    st.write("▼ 簡易CFと現預金の推移")
    st.line_chart(df_plot[["簡易CF", "現預金残高"]])

# --- 数値テーブル ---
st.subheader("詳細シミュレーション表")
st.dataframe(df_sim.style.format({
    "売上高": "{:,.0f}",
    "営業利益": "{:,.0f}",
    "簡易CF": "{:,.0f}",
    "借入金残高": "{:,.0f}",
    "現預金残高": "{:,.0f}"
}), use_container_width=True)

# CSVダウンロード
csv = df_sim.to_csv(index=False).encode('utf-8-sig')
st.download_button(
    label="結果をCSVで保存",
    data=csv,
    file_name='profit_debt_simulation.csv',
    mime='text/csv',
)
