これまでの実装内容をまとめた、実用的で分かりやすい `README.md` を作成しました。
プロジェクトのルートディレクトリに保存して使用してください。

---

# 🖥️ Amembo VM Controller

Streamlit を使用した、軽量かつ高機能な Proxmox VE 管理 Web インターフェースです。
LDAP 認証によるユーザー管理、物理ノードの Wake-on-LAN (WOL)、VM の排他制御機能を備えています。

## ✨ 主な機能

* **LDAP 認証:** AD や OpenLDAP と連携したセキュアなログイン（Search & Bind 方式対応）。
* **ホームディレクトリ自動作成:** 初回ログイン時、ユーザー専用のホームディレクトリを自動生成・権限設定（要 Root 権限）。
* **物理ノードの WOL 起動:** 停止している Proxmox ノードを API 経由で起動。接続失敗時に自動で WOL ボタンを表示。
* **VM 管理:**
* 起動 (WOL) / シャットダウン / 強制停止 (2段階操作)。
* QEMU Guest Agent 経由での IP アドレス取得・表示。


* **排他制御 (User Locking):**
* VM を起動したユーザーを「所有者」として記録。
* 他ユーザーによる誤ったシャットダウンを防止（所有者のみ操作可能）。


* **管理ノードの除外:** 特定の管理用ノード（例: `amembonas`）を操作リストから自動的に除外。

## 📦 必要要件

* Python 3.9+
* Proxmox VE Cluster (API 利用可能であること)
* LDAP Server (Active Directory, OpenLDAP, Synology Directory Server 等)
* 対象の VM に **QEMU Guest Agent** がインストールされ、有効化されていること。

## 🚀 インストール

1. **リポジトリのクローン**
```bash
git clone https://your-repository-url.git
cd amembo-vm-controller

```


2. **依存ライブラリのインストール**
```bash
pip install streamlit proxmoxer ldap3 urllib3 wakeonlan

```



## ⚙️ 設定

プロジェクトルートに `.streamlit/secrets.toml` ファイルを作成し、以下の内容を記述してください。
テンプレートがフォルダ内に用意されているので自由に加工してください

## ▶️ 実行方法

LDAP ユーザーのホームディレクトリ作成機能 (`chown` 等) を使用するため、**root 権限 (sudo)** で実行することを推奨します。

```bash
sudo streamlit run app.py

```

ブラウザで `http://<サーバーIP>:8501` にアクセスしてください。

## 📂 ファイル構成

```text
.
├── app.py                # エントリーポイント (ルーティング)
├── ui_login.py           # ログイン画面 UI
├── ui_main.py            # メイン操作画面 UI (ロジック含む)
├── auth_manager.py       # LDAP認証 & ホームディレクトリ作成ロジック
├── proxmox_manager.py    # Proxmox API 接続 & WOL & IP取得ロジック
├── state_manager.py      # 排他制御用の状態管理 (JSON保存)
├── vm_owners.json        # (自動生成) VM所有者の記録ファイル
└── .streamlit/
    └── secrets.toml      # 設定ファイル (Git管理外)

```

## ⚠️ 注意事項

1. **ネットワーク経路:**
* Streamlit が動作する環境から、Proxmox ノードのポート 8006 にアクセス可能である必要があります。
* コンテナ環境 (LXC/Docker) で実行する場合、ネットワーク設定にご注意ください。


2. **WOL の挙動:**
* WOL 機能は「生きている Proxmox ノード」を経由して API (`/wakeonlan`) を叩く方式を採用しています。クラスタ内の少なくとも 1 台が稼働している必要があります。


3. **排他制御の仕様:**
* 所有者情報は `vm_owners.json` に記録されます。
* Web UI 以外（Proxmox コンソール等）から VM を停止した場合、所有者記録が残る場合がありますが、次回起動時に上書きされます。



## 🐛 トラブルシューティング

* **IP アドレスが表示されない:**
* VM に `qemu-guest-agent` がインストールされているか確認してください。
* Proxmox の VM オプションで「QEMU Guest Agent」が有効になっているか確認してください。


* **"No route to host (595)" エラーが出る:**
* 指定した Proxmox ホストが停止している、またはネットワーク的に到達できない可能性があります。
* このエラーが出た場合でも、WOL パケット送信自体は成功している可能性があるため、数分待機してみてください。