import streamlit as st
from auth_manager import ldap_login

def render_login_page():
    """ログイン画面を描画する"""
    st.title("🖥️ Amembo VM Controller")
    
    with st.form("login_form"):
        st.subheader("LDAP Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            if ldap_login(username, password):
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.success("ログイン成功")
                st.rerun()
            else:
                st.error("ログイン失敗: ユーザー名またはパスワードが間違っています。")