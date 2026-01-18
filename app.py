import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import japanize_matplotlib  # 日本語化ライブラリ

# ページ設定
st.set_page_config(page_title="5ヵ年損益・資金推移シミュレーター", layout="wide")

st.title("📊 5ヵ年損益・資金推移シミュレーター")
st.caption("M4 MacBook Air 最適化版 / 単位：千円")

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
            "年目": "0 (期首)",
            "売上高": 0,
            "売上総利益": 0,
            "営業利益": 0,
            "減価償却費": 0,
            "簡易CF": 0,
            "借入金返済額": 0,
            "借入金残高": current_debt,
            "現預金残高": current_cash
        })
    else:
        revenue = rev_0
        gross_profit = revenue * gp_rate
        operating_profit = revenue * op_rate
        simple_cf = operating_profit + depreciation
        
        # 借入金返済：簡易CF（営業利益+償却費）と約定返済額で返済
        total_repayment_capacity = simple_cf + debt_repayment
        repayment_actual = min(current_debt, total_repayment_capacity)
        current_debt -= repayment_actual
        
        # 現預金推移（簡易：CF - 返済額を累積）
        current_cash += (simple_cf - debt_repayment)

        data.append({
            "年目": f"{year}年目",
            "売上高": revenue,
            "売上総利益": gross_profit,
            "営業利益": operating_profit,
            "減価償却費": depreciation,
            "簡易CF": simple_cf,
            "借入金返済額": debt_repayment,
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

# --- グラフ表示 ---
st.subheader("借入金残高と簡易CFの推移")
fig, ax1 = plt.subplots(figsize=(10, 5))

# 借入金残高（棒グラフ）
ax1.bar(df_sim["年目"], df_sim["借入金残高"], color="#FF9999", label="借入金残高", alpha=0.7)
ax1.set_ylabel("借入金残高 (千円)")
ax1.legend(loc="upper left")

# 簡易CF（折れ線グラフ）
ax2 = ax1.twinx()
ax2.plot(df_sim["年目"], df_sim["簡易CF"], color="#0066CC", marker="o", label="簡易CF (営業利益+償却費)")
ax2.set_ylabel("簡易CF (千円)")
ax2.legend(loc="upper right")

st.pyplot(fig)

# --- 数値テーブル ---
st.subheader("詳細シミュレーション表")
st.dataframe(df_sim.style.format({
    "売上高": "{:,.0f}",
    "売上総利益": "{:,.0f}",
    "営業利益": "{:,.0f}",
    "減価償却費": "{:,.0f}",
    "簡易CF": "{:,.0f}",
    "借入金返済額": "{:,.0f}",
    "借入金残高": "{:,.0f}",
    "現預金残高": "{:,.0f}"
}))

# CSVダウンロード
csv = df_sim.to_csv(index=False).encode('utf-8-sig')
st.download_button(
    label="シミュレーション結果をCSVでダウンロード",
    data=csv,
    file_name='profit_debt_simulation.csv',
    mime='text/csv',
)
