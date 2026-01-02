import streamlit as st
from ui.ui_login import render_login_page
from ui.ui_main import render_main_page

def main():
    st.set_page_config(page_title="Proxmox VM Manager", layout="centered")

    # セッション状態の初期化
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    # UI実装部
    if st.session_state['logged_in']:
        render_main_page()
    else:
        render_login_page()

if __name__ == "__main__":
    main()