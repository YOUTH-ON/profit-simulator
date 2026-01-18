import streamlit as st
import pandas as pd
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import io

# ページ設定
st.set_page_config(page_title="高度経営シミュレーター", layout="wide")

st.title("🏦 高度経営シミュレーター")
st.caption("M4 MacBook Air 最適化 / テンプレートCSV一括反映モデル")

# --- 1. ヘルパー関数: 設定データのシリアライズ/デシリアライズ ---
def export_config_to_csv(base_params, df_proj, df_act):
    """現在の全設定を1つのCSV文字列にまとめる"""
    output = io.StringIO()
    # セクション1: 基準値
    output.write("---BASIC_PARAMS---\n")
    pd.DataFrame([base_params]).to_csv(output, index=False)
    # セクション2: 案件明細
    output.write("---PROJECTS---\n")
    df_proj.to_csv(output, index=False)
    # セクション3: アクションプラン
    output.write("---ACTIONS---\n")
    df_act.to_csv(output, index=False)
    return output.getvalue()

def load_config_from_csv(csv_content):
    """CSV文字列を分割して各データフレーム/辞書に戻す"""
    sections = csv_content.split("---")
    data = {}
    for sec in sections:
        if sec.startswith("BASIC_PARAMS---"):
            data["params"] = pd.read_csv(io.StringIO(sec.replace("BASIC_PARAMS---\n", ""))).to_dict('records')[0]
        elif sec.startswith("PROJECTS---"):
            data["projects"] = pd.read_csv(io.StringIO(sec.replace("PROJECTS---\n", "")))
        elif sec.startswith("ACTIONS---"):
            data["actions"] = pd.read_csv(io.StringIO(sec.replace("ACTIONS---\n", "")))
    return data

# --- 2. セッション状態の初期化 ---
if "init_data" not in st.session_state:
    st.session_state.init_data = {
        "params": {"start_month": str(date.today().replace(day=1)), "init_cash": 10000.0, "gp_rate": 10.0, "op_rate": 3.0, "ord_rate": 3.0, "init_debt": 50000.0, "monthly_repayment": 500.0, "init_depr": 6000.0},
        "projects": pd.DataFrame([{"案件名": "既存案件A", "月額売上(千円)": 10000, "入金サイト(ヶ月)": 1}]),
        "actions": pd.DataFrame([{"計上種別": "売上高", "プラン名": "新規販路拡大", "月間効果額": 2000, "効果開始月": str(date.today() + relativedelta(months=6))}])
    }

# --- 3. サイドバー: 設定ファイルのインポート/エクスポート ---
with st.sidebar:
    st.header("設定ファイル管理")
    uploaded_file = st.file_uploader("テンプレートCSVをアップロード", type="csv")
    
    if uploaded_file:
        if st.button("設定を反映する"):
            content = uploaded_file.getvalue().decode("utf-8-sig")
            st.session_state.init_data = load_config_from_csv(content)
            st.rerun()

    st.divider()
    # 現在の状態を元にテンプレートを生成
    # ※計算用の一時変数から最新の状態を反映させるため、描画後に定義するのが理想的ですが
    # ここでは便宜上、現在のセッションデータから生成します。
    current_config_csv = export_config_to_csv(
        st.session_state.init_data["params"],
        st.session_state.init_data["projects"],
        st.session_state.init_data["actions"]
    )
    st.download_button("現在の設定をCSV保存", current_config_csv, "finance_template.csv", "text/csv")

# --- 4. 基準値入力 (セッション状態から読み込み) ---
p = st.session_state.init_data["params"]
st.subheader("📌 シミュレーション基準値")
with st.container(border=True):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        start_month = st.date_input("試算開始月", value=pd.to_datetime(p["start_month"]).date())
        init_cash = st.number_input("期首現預金残高", value=float(p["init_cash"]))
    with c2:
        gp_rate_val = st.number_input("売上総利益率 (%)", value=float(p["gp_rate"])) / 100
        op_rate_val = st.number_input("営業利益率 (%)", value=float(p["op_rate"])) / 100
        ord_rate_val = st.number_input("経常利益率 (%)", value=float(p["ord_rate"])) / 100
    with c3:
        init_debt = st.number_input("期首借入金残高", value=float(p["init_debt"]))
        monthly_repayment_input = st.number_input("借入金返済額 (月額)", value=float(p["monthly_repayment"]))
    with c4:
        init_depr_annual = st.number_input("減価償却費 (1年目年額)", value=float(p["init_depr"]))
        depr_decay_rate = 0.90

st.divider()

# --- 5. 案件別売上明細 & アクションプラン入力 ---
col_input1, col_input2 = st.columns(2)
with col_input1:
    st.subheader("📝 案件別売上明細")
    df_projects = st.data_editor(st.session_state.init_data["projects"], num_rows="dynamic", use_container_width=True, key="proj_editor")

with col_input2:
    st.subheader("🛠️ アクションプラン")
    action_categories = ["売上高", "売上原価", "販管費"]
    # 日付型の変換処理
    actions_loaded = st.session_state.init_data["actions"].copy()
    actions_loaded["効果開始月"] = pd.to_datetime(actions_loaded["効果開始月"]).dt.date
    
    df_actions = st.data_editor(
        actions_loaded, 
        num_rows="dynamic", 
        use_container_width=True, 
        key="action_editor",
        column_config={
            "計上種別": st.column_config.SelectboxColumn("計上種別", options=action_categories, required=True),
            "効果開始月": st.column_config.DateColumn("効果開始月", format="YYYY/MM", required=True)
        }
    )

# --- (以下、計算ロジックとレンダリング関数は前回の「配色統一版」を継承) ---
# ... (省略: 前回のdf_all生成ロジックおよびrender_financial_table関数をここに配置) ...
