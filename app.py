import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ページ設定
st.set_page_config(page_title="損益試算シミュレーター", layout="wide")

st.title("📊 損益試算シミュレーター")
st.caption("各数値を調整して、利益の推移をリアルタイムで確認できます。")

# --- サイドバー：入力パラメータ ---
st.sidebar.header("📈 入力パラメータ")

# 売上関連
st.sidebar.subheader("売上設定")
unit_price = st.sidebar.number_input("商品単価 (円)", value=1000, step=100)
sales_volume = st.sidebar.slider("販売数量 (月間)", 0, 10000, 1000)

# 原価関連
st.sidebar.subheader("原価設定")
cost_rate = st.sidebar.slider("原価率 (%)", 0, 100, 30) / 100

# 固定費関連
st.sidebar.subheader("固定費設定")
rent = st.sidebar.number_input("家賃 (円)", value=100000)
labor_cost = st.sidebar.number_input("人件費 (円)", value=200000)
other_fixed_costs = st.sidebar.number_input("その他固定費 (円)", value=50000)

# --- 計算ロジック ---
revenue = unit_price * sales_volume
variable_cost = revenue * cost_rate
fixed_cost = rent + labor_cost + other_fixed_costs
total_cost = variable_cost + fixed_cost
profit = revenue - total_cost
profit_margin = (profit / revenue * 100) if revenue > 0 else 0

# 損益分岐点計算
breakeven_volume = fixed_cost / (unit_price * (1 - cost_rate)) if (1 - cost_rate) > 0 else 0

# --- メイン画面：結果表示 ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("総売上", f"¥{revenue:,}")
col2.metric("総費用", f"¥{total_cost:,}")
col3.metric("営業利益", f"¥{profit:,}", delta=f"{profit:,}")
col4.metric("利益率", f"{profit_margin:.1f}%")

st.divider()

# --- グラフ表示 ---
st.subheader("損益構造の可視化")

# 棒グラフ用データ
labels = ['売上', '変動費', '固定費', '利益']
values = [revenue, variable_cost, fixed_cost, profit]
colors = ['#1f77b4', '#ff7f0e', '#d62728', '#2ca02c']

fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(labels, values, color=colors)
ax.set_ylabel("金額 (円)")

# 数値をラベル表示
for i, v in enumerate(values):
    ax.text(i, v + (max(values) * 0.02), f"¥{v:,}", ha='center')

st.pyplot(fig)

# --- 損益分岐点分析 ---
st.info(f"💡 **損益分岐点販売数量:** 約 {int(breakeven_volume):,} 個 （これ以上売ると黒字です）")

# 詳細データのテーブル表示
with st.expander("詳細データ表を確認"):
    df = pd.DataFrame({
        "項目": ["単価", "販売数量", "売上高", "変動費", "固定費", "営業利益"],
        "数値": [unit_price, sales_volume, revenue, variable_cost, fixed_cost, profit]
    })
    st.table(df)