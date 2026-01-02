import json
import os

STATE_FILE = ".tmp/vm_owners.json"

def load_state():
    """現在の所有者状態を読み込む"""
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_state(state):
    """状態を保存する"""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)

def set_vm_owner(node, vmid, username):
    """VMの所有者を記録する"""
    state = load_state()
    key = f"{node}_{vmid}"
    state[key] = username
    save_state(state)

def get_vm_owner(node, vmid):
    """VMの所有者を取得する"""
    state = load_state()
    key = f"{node}_{vmid}"
    return state.get(key) # 見つからなければ None を返す

def clear_vm_owner(node, vmid):
    """VMの所有者情報を削除する（シャットダウン時）"""
    state = load_state()
    key = f"{node}_{vmid}"
    if key in state:
        del state[key]
        save_state(state)