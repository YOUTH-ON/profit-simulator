import streamlit as st
import pandas as pd
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

# ページ設定
st.set_page_config(page_title="高度経営シミュレーター", layout="wide")

st.title("🏦 高度経営シミュレーター")
st.caption("M4 MacBook Air 最適化 / プレミアム・デザイン / エラー修正版")

# --- 1. 基準値入力 ---
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
        monthly_repayment_input = st.number_input("借入金返済額 (月額)", value=500)
    with c4:
        init_depr_annual = st.number_input("減価償却費 (1年目年額)", value=6000)
        depr_decay_rate = 0.90

st.divider()

# --- 2. 案件別売上明細 & アクションプラン入力 ---
col_input1, col_input2 = st.columns(2)
with col_input1:
    st.subheader("📝 案件別売上明細")
    default_projects = pd.DataFrame([{"案件名": "既存案件A", "月額売上(千円)": 10000, "入金サイト(ヶ月)": 1}])
    df_projects = st.data_editor(default_projects, num_rows="dynamic", use_container_width=True, key="proj_editor")
with col_input2:
    st.subheader("🛠️ アクションプラン")
    action_categories = ["売上高", "売上原価", "販管費"]
    default_actions = pd.DataFrame([{"計上種別": "売上高", "プラン名": "新規販路拡大", "月間効果額": 2000, "効果開始月": start_month + relativedelta(months=6)}])
    df_actions = st.data_editor(default_actions, num_rows="dynamic", use_container_width=True, key="action_editor")

# --- 3. 計算ロジック ---
months = 60
sim_data, current_debt, current_cash = [], init_debt, init_cash
plan_names = df_actions["プラン名"].tolist() if not df_actions.empty else []

for m in range(months):
    target_date = start_month + relativedelta(months=m)
    year_idx = m // 12
    monthly_depr = (init_depr_annual * (depr_decay_rate ** year_idx)) / 12
    base_revenue = df_projects["月額売上(千円)"].sum()
    
    action_rev, action_cos, action_sga, plan_impacts = 0, 0, 0, {name: 0 for name in plan_names}
    if not df_actions.empty:
        for _, row in df_actions.iterrows():
            if target_date >= pd.to_datetime(row["効果開始月"]).date():
                impact = row["月間効果額"]
                plan_impacts[row["プラン名"]] = impact
                if row["計上種別"] == "売上高": action_rev += impact
                elif row["計上種別"] == "売上原価": action_cos += impact
                elif row["計上種別"] == "販管費": action_sga += impact

    total_rev = base_revenue + action_rev
    total_cos = (base_revenue * (1 - gp_rate_val)) + action_cos
    total_gp, total_sga = total_rev - total_cos, (base_revenue * (gp_rate_val - op_rate_val)) + action_sga
    total_op = total_gp - total_sga
    total_ord = (total_rev * ord_rate_val) + (total_op - (base_revenue * op_rate_val))
    tax_base = max(0, total_ord)
    tax = (min(tax_base, 8000/12) * 0.15) + (max(0, tax_base - 8000/12) * 0.232)
    net_profit = total_ord - tax
    simple_cf = net_profit + monthly_depr
    actual_repayment = min(current_debt, float(monthly_repayment_input))
    current_debt -= actual_repayment
    cash_change = simple_cf - actual_repayment
    current_cash += cash_change
    
    res = {
        "年月": target_date.strftime("%Y/%m"), "売上高": total_rev, "売上総利益": total_gp, 
        "営業利益": total_op, "経常利益": total_ord, "当期純利益": net_profit, "簡易CF": simple_cf, 
        "月返済額": actual_repayment, "現預金残高": current_cash, "月商倍率": current_cash / total_rev if total_rev > 0 else 0
    }
    res.update(plan_impacts); sim_data.append(res)
df_all = pd.DataFrame(sim_data).fillna(0)

# --- 4. プレミアム・レンダリング関数 ---
def render_financial_table(df, height=400):
    # 表の中に実際に存在する列のみを対象にフォーマットを適用する
    available_cols = df.columns
    format_dict = {c: "{:,.0f}" for c in available_cols if c not in ["年月", "年度", "月商倍率"]}
    if "月商倍率" in available_cols:
        format_dict["月商倍率"] = "{:.2f}倍"
    
    style = df.style.format(format_dict).set_table_styles([
        {'selector': 'table', 'props': [('width', '100%'), ('border-collapse', 'collapse'), ('font-family', 'sans-serif'), ('font-size', '13px')]},
        {'selector': 'th', 'props': [('background-color', '#1E1E1E'), ('color', '#FFFFFF'), ('position', 'sticky'), ('top', '0'), ('z-index', '10'), ('padding', '12px'), ('text-align', 'center')]},
        {'selector': 'tr:nth-child(even)', 'props': [('background-color', 'rgba(128, 128, 128, 0.1)')]},
        {'selector': 'td', 'props': [('padding', '10px'), ('border-bottom', '1px solid rgba(128,128,128,0.2)'), ('text-align', 'right')]},
        {'selector': 'td:first-child', 'props': [('text-align', 'center'), ('font-weight', 'bold')]}
    ], overwrite=False)

    html = f"""
    <div style="height:{height}px; overflow:auto; border:1px solid rgba(128,128,128,0.2); border-radius:10px;">
        {style.to_html(index=False)}
    </div>
    """
    st.components.v1.html(html, height=height+20)

# --- 5. メイン表示 ---
tab1, tab2 = st.tabs(["📅 月次推移", "📊 年次まとめ"])
with tab1:
    st.subheader("📋 損益・資金繰り計画 (月次)")
    render_financial_table(df_all)

with tab2:
    # 集計ロジックの修正: 存在するすべての数値列を合計し、現預金残高は期末残高をとる
    df_all['年度'] = df_all['年月'].apply(lambda x: x[:4] + "年度")
    
    # 合計すべき列（売上、利益、簡易CF、返済、および各プランの列）
    agg_cols = ['売上高', '売上総利益', '営業利益', '経常利益', '当期純利益', '簡易CF', '月返済額'] + plan_names
    agg_dict = {col: 'sum' for col in agg_cols if col in df_all.columns}
    agg_dict['現預金残高'] = 'last' # 残高だけは「合計」ではなく「期末」
    
    df_yearly = df_all.groupby('年度').agg(agg_dict).reset_index()
    df_yearly['月商倍率'] = df_yearly['現預金残高'] / (df_yearly['売上高'] / 12)
    
    st.subheader("📊 年度別サマリー")
    render_financial_table(df_yearly, height=300)
    st.line_chart(df_yearly.set_index('年度')[['現預金残高']])

st.download_button("CSV出力", df_all.to_csv(index=False).encode('utf-8-sig'), "finance_sim.csv")
