import streamlit as st
import time
from proxmox_manager import get_proxmox_conn, get_vm_ip, wake_node
from state_manager import set_vm_owner, get_vm_owner, clear_vm_owner

def render_main_page():
    """メインのProxmox操作画面を描画する"""
    st.title("🖥️ Amembo VM Controller")

    # --- サイドバー ---
    st.sidebar.success(f"User: {st.session_state.get('username', 'Unknown')}")
    if st.sidebar.button("Logout", key="sidebar_logout"): # keyを追加
        st.session_state['logged_in'] = False
        st.rerun()

    # 変数の初期化
    prox = None
    is_api_reachable = False
    node_list = []

    # --- 1. Proxmox API接続 & ノード取得 ---
    try:
        prox = get_proxmox_conn()
        all_nodes = prox.nodes.get()
        
        # 管理ノード除外
        exclude_name = "amembonas"
        node_list = [n['node'] for n in all_nodes if n['node'].lower() != exclude_name.lower()]
        is_api_reachable = True

    except Exception:
        is_api_reachable = False
        node_list = ["Amembo"]

    # --- 2. ノード選択 ---
    selected_node = st.selectbox("ノード選択", node_list)

    # --- 3. アクション分岐 ---
    if selected_node:
        if not is_api_reachable:
            show_offline_controls(selected_node, "サーバーに接続できません。電源が落ちている可能性があります。")
        else:
            try:
                # VM一覧を取得
                vms = prox.nodes(selected_node).qemu.get()
                vm_options = {f"{vm['vmid']}: {vm['name']} ({vm['status']})": vm for vm in vms if vm.get('template') != 1}
                
                selected_vm_label = st.selectbox("VMを選択してください", options=list(vm_options.keys()))
                
                if selected_vm_label:
                    vm_data = vm_options[selected_vm_label]
                    render_vm_controls(prox, selected_node, vm_data)
                    
            except Exception as e:
                st.warning(f"⚠️ ノード '{selected_node}' から応答がありません")
                show_offline_controls(selected_node, "ノードが停止している場合は、以下のボタンで起動してください。")

def show_offline_controls(node_name, message):
    """オフライン時にWOLボタンを表示する共通関数"""
    st.divider()
    st.info(message)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        # key にノード名を含めて一意にする
        if st.button(f"⚡ {node_name} を起動 (WOL)", type="primary", key=f"wol_node_{node_name}"):
            with st.spinner(f"{node_name} に起動コマンド(WOL)を送信中..."):
                success, msg = wake_node(node_name)
                if success:
                    st.success(msg)
                    st.info("起動には数分かかります。しばらく待ってから「再接続」してください。")
                else:
                    st.error(msg)
    
    with col2:
        # key を追加
        if st.button("🔄 再接続 (リロード)", key=f"reload_node_{node_name}"):
            st.rerun()

def render_vm_controls(prox, node, vm_data):
    """個別のVM操作パネルを描画するヘルパー関数"""
    vmid = vm_data['vmid']
    vm_name = vm_data['name']
    status = vm_data['status']
    
    current_user = st.session_state.get('username')
    owner = get_vm_owner(node, vmid)
    shutdown_key = f"shutdown_triggered_{vmid}"

    if status == "stopped" and shutdown_key in st.session_state:
        del st.session_state[shutdown_key]

    st.divider()
    st.subheader(f"VM詳細: {vm_name}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Status", status.upper(), delta="Running" if status == "running" else "Stopped")
        if status == "running":
            if owner:
                if owner == current_user:
                    st.caption(f"👤 **あなた** が使用中です")
                else:
                    st.warning(f"🔒 **{owner}** さんが使用中です")
            else:
                st.caption("👤 使用者は記録されていません")

    with col2:
        if status == "stopped":
            # --- 起動処理 ---
            # key に vmid を含める！これで別のVMのボタンと混同されない
            if st.button("🚀 VM起動 (WOL)", type="primary", key=f"btn_start_{vmid}"):
                with st.spinner(f"{vm_name} (ID:{vmid}) を起動しています..."):
                    try:
                        prox.nodes(node).qemu(vmid).status.start.post()
                        set_vm_owner(node, vmid, current_user)
                        st.success("起動コマンドを送信しました！")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"起動エラー: {e}")
        
        elif status == "running":
            # --- 停止処理 ---
            can_shutdown = False
            if owner is None or owner == current_user:
                can_shutdown = True
            
            if can_shutdown:
                if shutdown_key not in st.session_state:
                    # 1回目: シャットダウン (keyにvmidを含める)
                    if st.button("🛑 シャットダウン", key=f"btn_shutdown_{vmid}"):
                        try:
                            prox.nodes(node).qemu(vmid).status.shutdown.post()
                            st.session_state[shutdown_key] = True
                            clear_vm_owner(node, vmid)
                            st.warning("信号送信済み。強制停止する場合はもう一度押してください。")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                             st.error(f"終了エラー: {e}")
                else:
                    # 2回目: 強制停止 (keyにvmidを含める)
                    st.warning("⚠️ シャットダウン信号送信済み")
                    if st.button("⚡ 強制停止 (STOP)", type="primary", key=f"btn_stop_{vmid}"):
                        try:
                            prox.nodes(node).qemu(vmid).status.stop.post()
                            del st.session_state[shutdown_key]
                            clear_vm_owner(node, vmid)
                            st.error("強制停止コマンドを送信しました。")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"停止エラー: {e}")
            else:
                st.error("🚫 他のユーザーが使用中のため操作できません")

    if status == "running":
        st.info("IPアドレスを取得中...")
        ip_list = get_vm_ip(prox, node, vmid)
        if ip_list:
            st.success(f"IP Address: {', '.join(ip_list)}")
        else:
            st.warning("IPアドレスが取得できません。")
            # key に vmid を含める
            if st.button("🔄 IP再取得", key=f"btn_refresh_ip_{vmid}"):
                st.rerun()