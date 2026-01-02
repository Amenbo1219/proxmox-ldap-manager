import streamlit as st
from proxmoxer import ProxmoxAPI
import urllib3
# wakeonlan はAPI経由にするなら不要ですが、念のためimport残してもOK

# 自己署名証明書の警告を抑制
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@st.cache_resource
def get_proxmox_conn():
    """Proxmox APIへの接続を確立する"""
    pm_conf = st.secrets["proxmox"]
    port = pm_conf.get("port", 8006)

    prox = ProxmoxAPI(
        pm_conf["host"],
        user=pm_conf["user"],
        password=pm_conf["password"],
        verify_ssl=pm_conf["verify_ssl"],
        port=port,
        timeout=10
    )
    return prox

def wake_node(node_name):
    """生きているProxmoxノード経由で、指定されたノードをWOL起動する"""
    try:
        prox = get_proxmox_conn()
        prox.nodes(node_name).wakeonlan.post()
        return True, f"Proxmox API経由で起動コマンドを送信しました: {node_name}"

    except Exception as e:
        error_str = str(e)
        if "595" in error_str:
             return True, f"起動コマンドを送信しました (応答: {e})。\n数分待ってから確認してください。"
        return False, f"API WOL送信エラー: {e}"

def get_vm_ip(prox, node, vmid):
    """QEMU Guest Agent経由でIPを取得する"""
    try:
        data = prox.nodes(node).qemu(vmid).agent('network-get-interfaces').get()
        ip_list = []
        if 'result' in data:
            for iface in data['result']:
                if iface.get('name') == 'lo':
                    continue
                
                for ip_info in iface.get('ip-addresses', []):
                    ip_addr = ip_info.get('ip-address')
                    ip_type = ip_info.get('ip-address-type')
                    if ip_type == 'ipv4' and ip_addr != '127.0.0.1':
                        ip_list.append(ip_addr)
        return ip_list

    except Exception as e:
        return None