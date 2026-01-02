import streamlit as st
import os
from ldap3 import Server, Connection, SIMPLE

def create_user_home(path, uid, gid):
    """
    ホームディレクトリが存在しない場合に作成し、権限を設定する
    注意: chownを実行するにはroot権限が必要です
    """
    try:
        if not os.path.exists(path):
            # ホームディレクトリ作成＆ユーザー権限以降
            os.makedirs(path, exist_ok=True)
            os.chmod(path, 0o700)
            os.chown(path, int(uid), int(gid))
            
            print(f"✅ ホームディレクトリを作成しました: {path} (UID:{uid}, GID:{gid})")
    except PermissionError:
        st.error(f"⚠️ 権限エラー: ホームディレクトリ '{path}' の作成または所有者変更に失敗しました。アプリをroot権限で実行していますか？")
    except Exception as e:
        st.error(f"⚠️ ホームディレクトリ作成エラー: {e}")

def ldap_login(username, password):
    """LDAPサーバーで検索してから認証を行う (Search & Bind)"""
    try:
        ldap_config = st.secrets["ldap"]
        server = Server(ldap_config["server"], get_info='ALL')
        
        # 1. 管理者(bind_dn)で接続する
        conn = Connection(server, 
                          user=ldap_config["bind_dn"], 
                          password=ldap_config["bind_password"], 
                          auto_bind=True)
        
        # 2. ユーザーを検索する
        # ここでホームディレクトリ情報とUID/GIDも一緒に取得します
        search_filter = f"(uid={username})"
        conn.search(
            ldap_config["base_dn"], 
            search_filter, 
            attributes=['cn', 'homeDirectory', 'uidNumber', 'gidNumber']
        )
        
        if len(conn.entries) > 0:
            user_entry = conn.entries[0]
            user_dn = user_entry.entry_dn
            
            # 3. 本人確認（パスワード検証）
            user_conn = Connection(server, user=user_dn, password=password)
            if user_conn.bind():
                # 認証成功時にユーザー情報の取得
                home_dir = str(user_entry.homeDirectory) if 'homeDirectory' in user_entry else None
                uid = str(user_entry.uidNumber) if 'uidNumber' in user_entry else None
                gid = str(user_entry.gidNumber) if 'gidNumber' in user_entry else None

                if home_dir and uid and gid:
                    create_user_home(home_dir, uid, gid)
                else:
                    print("⚠️ LDAPにホームディレクトリ情報などが不足しているため作成をスキップしました")

                return True
            else:
                return False
        else:
            print("ユーザーが見つかりませんでした")
            return False
            
    except Exception as e:
        st.error(f"LDAP Error: {e}")
        return False