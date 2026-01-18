import streamlit as st
import pandas as pd
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import io

# ページ設定
st.set_page_config(page_title="高度経営シミュレーター", layout="wide")

st.title("🏦 高度経営シミュレーター")
st.caption("M4 MacBook Air 最適化 / 冒頭3行のみ読み込み・安定モデル")

# --- 1. セッション状態の初期化 ---
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

# --- 2. 修正版: CSV読み込みロジック (冒頭のみ抽出) ---
def load_simple_initial_values(csv_content):
    """CSVの冒頭部分から基準値、案件、アクションの1行目のみを取得する"""
    try:
        sections = csv_content.split("---")
        new_data = st.session_state.init_data.copy()
        
        for sec in sections:
            sec = sec.strip()
            if not sec: continue
            
            # 各セクションのデータを読み込み、4行目以降（データとしては2行目以降）を切り捨てる
            if sec.startswith("BASIC_PARAMS"):
                content = sec.replace("BASIC_PARAMS\n", "")
                df = pd.read_csv(io.StringIO(content)).head(1) # 1行目(初期値)のみ
                if not df.empty:
                    new_data["params"] = df.to_dict('records')[0]
            
            elif sec.startswith("PROJECTS"):
                content = sec.replace("PROJECTS\n", "")
                new_data["projects"] = pd.read_csv(io.StringIO(content)).head(1) # 1行目(初期値)のみ
            
            elif sec.startswith("ACTIONS"):
                content = sec.replace("ACTIONS\n", "")
                new_data["actions"] = pd.read_csv(io.StringIO(content)).head(1) # 1行目(初期値)のみ
                
        return new_data
    except Exception as e:
        st.error(f"パースエラー: {e}")
        return st.session_state.init_data

# --- 3. サイドバー: インポート機能 ---
with st.sidebar:
    st.header("⚙️ 初期値インポート")
    uploaded_file = st.file_uploader("CSVをアップロード", type="csv")
    
    if uploaded_file:
        if st.button("初期値を反映する"):
            content = uploaded_file.getvalue().decode("utf-8-sig")
            st.session_state.init_data = load_simple_initial_values(content)
            st.success("初期値を反映しました。")
            st.rerun()

# --- 4. 入力インターフェース (前回のロジックを維持) ---
p = st.session_state.init_data.get("params", {})

# ... (中略: シミュレーション基準値、案件エディタ、アクションプランエディタの描画) ...

# ---------------------------------------------------------
# 計算ロジック・レンダリング関数は前回のものを継承
# ---------------------------------------------------------
