import streamlit as st
import pandas as pd
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

# ページ設定
st.set_page_config(page_title="高度経営シミュレーター", layout="wide")

st.title("🚀 高度経営シミュレーター (アクションプラン対応版)")
st.caption("M4 MacBook Air 最適化 / アクションプラン連動ロジック搭載 / 単位：千円")

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
    default_projects = pd.DataFrame([
        {"案件名": "既存案件A", "月額売上(千円)": 10000, "入金サイト(ヶ月)": 1},
    ])
    df_projects = st.data_editor(default_projects, num_rows="dynamic", use_container_width=True, key="proj_editor")

with col_input2:
    st.subheader("🛠️ アクションプラン")
    action_categories = ["売上高", "売上原価", "販管費"]
    default_actions = pd.DataFrame([
        {"計上種別": "売上高", "プラン名": "新規販路拡大", "プラン内容": "Webマーケ強化", "月間効果額": 2000, "効果開始月": start_month + relativedelta(months=6)},
        {"計上種別": "売上原価", "プラン名": "仕入ルート見直し", "プラン内容": "バルク買い", "月間効果額": -500, "効果開始月": start_month + relativedelta(months=3)},
    ])
    df_actions = st.data_editor(
        default_actions,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "計上種別": st.column_config.SelectboxColumn(options=action_categories, required=True),
            "効果開始月": st.column_config.DateColumn(format="YYYY/MM")
        },
        key="action_editor"
    )

st.divider()

# --- 3. 計算ロジック ---
months = 60
sim_data = []
current_debt = init_debt
current_cash = init_cash
collection_schedule = {}

for m in range(months):
    target_date = start_month + relativedelta(months=m)
    year_idx = m // 12
    
    # 減価償却
    current_annual_depr = init_depr_annual * (depr_decay_rate ** year_idx)
    monthly_depr = current_annual_depr / 12
    
    # 基本の損益（案件明細から）
    base_revenue = df_projects["月額売上(千円)"].sum()
    
    # アクションプランの反映
    action_rev = 0
    action_cos = 0
    action_sga = 0
    plan_impacts = {} # 内数表示用

    if not df_actions.empty:
        for _, row in df_actions.iterrows():
            if target_date >= pd.to_datetime(row["効果開始月"]).date():
                impact = row["月間効果額"]
                plan_impacts[row["プラン名"]] = impact
                if row["計上種別"] == "売上高":
                    action_rev += impact
                elif row["計上種別"] == "売上原価":
                    action_cos += impact
                elif row["計上種別"] == "販管費":
                    action_sga += impact

    # 最終損益計算
    total_rev = base_revenue + action_rev
    total_cos = (base_revenue * (1 - gp_rate_val)) + action_cos
    total_gp = total_rev - total_cos
    total_sga = (base_revenue * (gp_rate_val - op_rate_val)) + action_sga
    total_op = total_gp - total_sga
    total_ord = (total_rev * ord_rate_val) + (total_op - (base_revenue * op_rate_val)) # 営業外を一定と仮定
    
    # 税金・純利益
    tax_base = max(0, total_ord)
    tax = (min(tax_base, 8000/12) * 0.15) + (max(0, tax_base - 8000/12) * 0.232)
    net_profit = total_ord - tax
    
    # キャッシュフロー
    for _, row in df_projects.iterrows():
        c_date = target_date + relativedelta(months=int(row["入金サイト(ヶ月)"]))
        collection_schedule[c_date] = collection_schedule.get(c_date, 0) + row["月額売上(千円)"]
    
    cash_in = collection_schedule.get(target_date, 0) + action_rev # プラン売上は即金と仮定
    actual_repayment = min(current_debt, float(monthly_repayment_input))
    current_debt -= actual_repayment
    
    # 現金支出 = 売上原価 + 販管費 - 減価償却費 (非現金)
    cash_out_expenses = total_cos + total_sga - monthly_depr
    current_cash = current_cash + cash_in - cash_out_expenses - tax - actual_repayment
    
    # データの格納
    res = {
        "年度": f"{year_idx + 1}年目", "年月": target_date.strftime("%Y/%m"),
        "売上高": total_rev, "売上原価": total_cos, "売上総利益": total_gp, "売上総利益率": total_gp/total_rev if total_rev!=0 else 0,
        "販管費": total_sga, "営業利益": total_op, "営業利益率": total_op/total_rev if total_rev!=0 else 0,
        "経常利益": total_ord, "経常利益率": total_ord/total_rev if total_rev!=0 else 0,
        "法人税等": tax, "当期純利益": net_profit, "減価償却費": monthly_depr,
        "簡易CF": net_profit + monthly_depr, "返済額": actual_repayment, "借入金残高": current_debt, "現預金残高": current_cash
    }
    # アクションプランの内数を追加
    res.update(plan_impacts)
    sim_data.append(res)

df_all = pd.DataFrame(sim_data).fillna(0)

# --- 4. 表示用処理 ---
def format_df(df):
    cols = df.columns
    format_dict = {c: "{:,.0f}" for c in cols if c not in ["年度", "年月", "売上総利益率", "営業利益率", "経常利益率"]}
    format_dict.update({"売上総利益率": "{:.1%}", "営業利益率": "{:.1%}", "経常利益率": "{:.1%}", "減価償却費": "{:,.1f}", "簡易CF": "{:,.1f}"})
    return df.style.format(format_dict)

tab1, tab2 = st.tabs(["📅 月次シミュレーション", "📊 年次サマリー"])

with tab1:
    st.subheader("📋 損益試算表 (月次)")
    plan_names = df_actions["プラン名"].tolist() if not df_actions.empty else []
    pl_base_cols = ["年月", "売上高", "売上原価", "売上総利益", "売上総利益率", "販管費", "営業利益", "営業利益率", "経常利益", "経常利益率", "法人税等", "当期純利益"]
    # プラン名を内数として列に含める
    pl_display_cols = pl_base_cols + plan_names
    st.dataframe(format_df(df_all[pl_display_cols]), use_container_width=True)
    
    st.subheader("📋 簡易CF計算書 (月次)")
    cf_cols = ["年月", "当期純利益", "減価償却費", "簡易CF", "返済額", "借入金残高", "現預金残高"]
    st.dataframe(format_df(df_all[cf_cols]), use_container_width=True)

with tab2:
    # 年次集計
    agg_dict = {c: "sum" for c in df_all.columns if c not in ["年度", "年月", "売上総利益率", "営業利益率", "経常利益率", "借入金残高", "現預金残高"]}
    agg_dict.update({"借入金残高": "last", "現預金残高": "last"})
    df_yearly = df_all.groupby("年度").agg(agg_dict).reset_index()
    
    # 比率再計算
    for p in ["売上総利益", "営業利益", "経常利益"]:
        df_yearly[f"{p}率"] = df_yearly[p] / df_yearly["売上高"]

    st.subheader("📊 年次損益試算表")
    st.dataframe(format_df(df_yearly[["年度"] + pl_base_cols[1:] + plan_names]), use_container_width=True)
    
    st.subheader("📊 年次簡易CF計算書")
    st.dataframe(format_df(df_yearly[["年度"] + cf_cols[1:]]), use_container_width=True)
    
    st.line_chart(df_yearly.set_index("年度")[["現預金残高", "借入金残高"]])

# CSV
st.download_button("CSV保存", df_all.to_csv(index=False).encode('utf-8-sig'), "sim_full.csv", "text/csv")
