import streamlit as st
import pandas as pd
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import io

# ページ設定
st.set_page_config(page_title="高度経営シミュレーター", layout="wide")

st.title("🏦 高度経営シミュレーター")
st.caption("M4 MacBook Air 最適化 / KeyError対策済み・安定版")

# --- 1. セッション状態の初期化ロジック ---
# 構造を固定し、読み込み失敗時でもエラーにならないようにします
if "init_data" not in st.session_state:
    st.session_state.init_data = {
        "params": {
            "start_month": str(date.today().replace(day=1)),
            "init_cash": 10000.0,
            "gp_rate": 10.0,
            "op_rate": 3.0,
            "ord_rate": 3.0,
            "init_debt": 50000.0,
            "monthly_repayment": 500.0,
            "init_depr": 6000.0
        },
        "projects": pd.DataFrame([{"案件名": "既存案件A", "月額売上(千円)": 10000, "入金サイト(ヶ月)": 1}]),
        "actions": pd.DataFrame([{"計上種別": "売上高", "プラン名": "新規販路拡大", "月間効果額": 2000, "効果開始月": str(date.today() + relativedelta(months=6))}])
    }

# --- 2. 設定ファイルのシリアライズ関数 ---
def export_config_to_csv():
    output = io.StringIO()
    # 基準値
    output.write("---BASIC_PARAMS---\n")
    pd.DataFrame([st.session_state.init_data["params"]]).to_csv(output, index=False)
    # 案件明細
    output.write("---PROJECTS---\n")
    st.session_state.init_data["projects"].to_csv(output, index=False)
    # アクションプラン
    output.write("---ACTIONS---\n")
    st.session_state.init_data["actions"].to_csv(output, index=False)
    return output.getvalue()

def load_config_from_csv(csv_content):
    sections = csv_content.split("---")
    new_data = st.session_state.init_data.copy() # デフォルト値でバックアップ
    
    for sec in sections:
        sec = sec.strip()
        if sec.startswith("BASIC_PARAMS"):
            content = sec.replace("BASIC_PARAMS\n", "")
            new_data["params"] = pd.read_csv(io.StringIO(content)).to_dict('records')[0]
        elif sec.startswith("PROJECTS"):
            content = sec.replace("PROJECTS\n", "")
            new_data["projects"] = pd.read_csv(io.StringIO(content))
        elif sec.startswith("ACTIONS"):
            content = sec.replace("ACTIONS\n", "")
            new_data["actions"] = pd.read_csv(io.StringIO(content))
    return new_data

# --- 3. サイドバー: インポート/エクスポート ---
with st.sidebar:
    st.header("⚙️ 設定ファイル管理")
    uploaded_file = st.file_uploader("CSVをアップロード", type="csv")
    
    if uploaded_file:
        if st.button("設定を反映する"):
            try:
                content = uploaded_file.getvalue().decode("utf-8-sig")
                st.session_state.init_data = load_config_from_csv(content)
                st.success("設定を反映しました。再読み込みします...")
                st.rerun() # 最新のStreamlitでは st.rerun() を使用
            except Exception as e:
                st.error(f"読み込みエラー: {e}")

    st.divider()
    st.download_button(
        label="現在の設定をCSV保存",
        data=export_config_to_csv(),
        file_name=f"finance_config_{date.today()}.csv",
        mime="text/csv"
    )

# --- 4. データの取得 (KeyError防止のため get メソッドを使用) ---
p = st.session_state.init_data.get("params", {})

st.subheader("📌 シミュレーション基準値")
with st.container(border=True):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        # 文字列の日付をdate型に変換
        sd = pd.to_datetime(p.get("start_month", date.today())).date()
        start_month = st.date_input("試算開始月", value=sd)
        init_cash = st.number_input("期首現預金残高", value=float(p.get("init_cash", 0)))
    with c2:
        gp_rate_val = st.number_input("売上総利益率 (%)", value=float(p.get("gp_rate", 0))) / 100
        op_rate_val = st.number_input("営業利益率 (%)", value=float(p.get("op_rate", 0))) / 100
        ord_rate_val = st.number_input("経常利益率 (%)", value=float(p.get("ord_rate", 0))) / 100
    with c3:
        init_debt = st.number_input("期首借入金残高", value=float(p.get("init_debt", 0)))
        monthly_repayment_input = st.number_input("借入金返済額 (月額)", value=float(p.get("monthly_repayment", 0)))
    with c4:
        init_depr_annual = st.number_input("減価償却費 (1年目年額)", value=float(p.get("init_depr", 0)))
        depr_decay_rate = 0.90

# --- 5. 入力エディタ ---
col_input1, col_input2 = st.columns(2)
with col_input1:
    st.subheader("📝 案件別売上明細")
    df_projects = st.data_editor(st.session_state.init_data["projects"], num_rows="dynamic", use_container_width=True, key="proj_editor")

with col_input2:
    st.subheader("🛠️ アクションプラン")
    # 日付列の型変換（これを行わないと DateColumn でエラーが出る場合がある）
    actions_df = st.session_state.init_data["actions"].copy()
    actions_df["効果開始月"] = pd.to_datetime(actions_df["効果開始月"]).dt.date
    
    df_actions = st.data_editor(
        actions_df,
        num_rows="dynamic",
        use_container_width=True,
        key="action_editor",
        column_config={
            "計上種別": st.column_config.SelectboxColumn("計上種別", options=["売上高", "売上原価", "販管費"], required=True),
            "効果開始月": st.column_config.DateColumn("効果開始月", format="YYYY/MM", required=True)
        }
    )

# ---------------------------------------------------------
# 以降の「3. 計算ロジック」と「4. レンダリング関数」は
# 前回のコード（配色統一版）をそのまま使用してください。
# ---------------------------------------------------------
