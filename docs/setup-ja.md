# 別の Linux 環境で ChatGPT Web から Poyto を使う

移行先の Linux マシンで再現するための手順です。現在の開発マシンのパス、Tunnel ID、キー、インストール済みプラグインには依存しません。コマンドは特記がない限り、**移行先の Bash** で実行します。

```text
ChatGPT Web → OpenAI Secure MCP Tunnel → 移行先の tunnel-client
           → Poyto MCP サーバー → POYP API / 移行先のファイル・シェル
```

Chat On Steroids、Chrome 拡張、Codex アプリは必須ではありません。Poyto は非公式クライアントです。[免責事項](../DISCLAIMER.md)も確認してください。

## 1. 必要なもの

- Linux、Bash、Git、Python 3.10～3.14、venv/pip
- ChatGPT Web の Developer mode とカスタム MCP 接続を利用できるアカウント
- OpenAI Platform の Tunnel 作成・使用権限
- 利用を許可された POYP セッション JSON、またはログイン応答を含む HAR/HAR.zip
- 移行先から OpenAI と POYP への外向き HTTPS 通信

まず Python を直接動かす **stdio 構成** を説明します。公開 MCP ポートは不要です。シェルは起動した Linux ユーザーの権限で動きます。ファイルツールのルート制限はシェル全体のサンドボックスではありません。Docker 構成は後半に記載します。

## 2. Poyto をインストール

```bash
mkdir -p "$HOME/apps"
git clone https://github.com/tqmane/Poyto.git "$HOME/apps/Poyto"
cd "$HOME/apps/Poyto"
test -f scripts/run-plugin-stdio.sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[agent]'
.venv/bin/poyto-plugin --help
```

この手順に対応した変更を含むコミット／配布ソースを使ってください。`scripts/run-plugin-stdio.sh` がない、または `--transport stdio` が表示されない場合は古い版です。未公開の変更を移す場合は変更済みソースも移し、`.venv` は移行先で作り直します。仮想環境や秘密ファイルは Git に含めません。

以降の値を設定します。**別のターミナルで再開するときも、この変数設定を実行します。**

```bash
poyto_repo="$HOME/apps/Poyto"
poyto_key_file="$HOME/.config/poyto-tunnel/runtime.key"
export POYTO_SESSION_FILE="$HOME/.local/state/poyto/session.json"
export PATH="$HOME/.local/bin:$PATH"
```

## 3. POYP のログイン情報を設定

### 保存済みセッション JSON を使う

SSH/SCP などで移行先の私有フォルダーへ転送し、転送先を次の `/absolute/private/path/session.json` に指定します。

```bash
install -d -m 700 "$(dirname "$POYTO_SESSION_FILE")"
install -m 600 /absolute/private/path/session.json "$POYTO_SESSION_FILE"
```

JSON は Poyto が保存する形式（`access_token`、利用可能なら `refresh_token` と有効期限情報を含む）です。ファイル名は `android-session.json` でも構いません。すでに適切な場所にある場合は、コピーせず `POYTO_SESSION_FILE` にその絶対パスを設定できます。

### HAR/HAR.zip から初期設定する

上の JSON コピーの代わりに実行します。

```bash
install -d -m 700 "$(dirname "$POYTO_SESSION_FILE")"
"$poyto_repo/.venv/bin/poyto" login --har /absolute/private/path/capture.har.zip
```

### 移行先で読み取りを確認

```bash
"$poyto_repo/.venv/bin/poyto" balances
```

結果には自分の残高が表示されます。セッションや HAR の中身を ChatGPT に貼る必要はありません。

refresh 後の保存にも同じパスを使うので、実行ユーザーがファイルと親ディレクトリに書き込める必要があります。移行時は旧環境の利用を止めてから最新セッションを移し、同じ refresh token を複数マシンで同時使用しないでください。無効になった refresh token は再ログインなどによる更新が必要です。詳細は[認証](authentication.md)と[refresh の挙動](refresh-tokens.md)を参照してください。

## 4. Tunnel と実行用キーを用意

1. [Platform → Tunnels](https://platform.openai.com/settings/organization/tunnels) で移行先用の Tunnel を作成します。
2. 利用する ChatGPT ワークスペースを関連付け、Tunnel ID を控えます。作成・編集には Tunnels の **Read + Manage** が必要です。
3. [API キー設定](https://platform.openai.com/settings/organization/api-keys)で、Tunnels の **Read + Use** を持つ実行用キーを用意します。

この OpenAI キーは POYP の token とは別物です。既存の Tunnel を引き継ぐ場合は旧環境のクライアントを停止してから移行先を起動します。旧環境も使うなら移行先専用の Tunnel と ChatGPT 接続を作ります。

以下は、キーを履歴や画面に残さずファイルへ保存する初回用のコマンドです。すでに保存済みなら省略してください。既存ファイルは上書きしません。

```bash
python3 - <<'PY'
import getpass
import os
from pathlib import Path

path = Path.home() / ".config/poyto-tunnel/runtime.key"
path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
key = getpass.getpass("OpenAI Tunnel runtime key: ").strip()
if not key:
    raise SystemExit("キーが空です")
fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, "w") as stream:
    stream.write(key + "\n")
print("キーを私有ファイルに保存しました")
PY
```

## 5. tunnel-client をインストールして接続

[Platform の Tunnel ページ](https://platform.openai.com/settings/organization/tunnels)または[OpenAI 公式リリース](https://github.com/openai/tunnel-client/releases/latest)から、移行先の OS・CPU に対応するアーカイブを取得します。公開チェックサムを照合して展開し、その中の `tunnel-client` をインストールします。

```bash
install -d "$HOME/.local/bin"
install -m 755 /absolute/path/to/extracted/tunnel-client "$HOME/.local/bin/tunnel-client"
tunnel-client --version
tunnel-client help quickstart
```

以下のコマンド形は tunnel-client 0.0.14 で確認しています。版によってオプションが変わった場合は公式 quickstart に従います。`tunnel_...` は自分の Tunnel ID に置き換えてください。

```bash
poyto_tunnel_id='tunnel_REPLACE_WITH_YOUR_ID'
tunnel-client runtimes connect \
  --alias poyto --profile poyto \
  --tunnel-id "$poyto_tunnel_id" \
  --runtime-api-key "file:$poyto_key_file" \
  --mcp-command "env POYTO_SESSION_FILE='$POYTO_SESSION_FILE' bash '$poyto_repo/scripts/run-plugin-stdio.sh'"
tunnel-client runtimes status poyto --json
```

`process_running`、`healthy`、`ready` がすべて `true` になることを確認します。`tunnel-client` が Poyto を起動するため、別途 `poyto-plugin` を常駐させる必要はありません。

ファイルツールの対象は既定でチェックアウト先です。変更する場合は上の `env` に `POYTO_PLUGIN_ROOTS='/absolute/workspace:/another/allowed/root'` を追加します。

この起動はターミナル終了後も継続しますが、OS 再起動後の自動起動は別途設定します。

## 6. ChatGPT Web に登録

1. **設定 → セキュリティとログイン → Developer mode** を有効にします。
2. [プラグイン](https://chatgpt.com/plugins)の **＋／アプリを作成**を選びます。
3. 名前を `Poyto Server Control` などに設定します。
4. 接続で **トンネル**を選び、移行先用の Tunnel を指定します。
5. この stdio 構成では MCP の認証に **認証なし**を選びます。接続へのアクセスは Secure MCP Tunnel が認証します。
6. ファイル操作・シェルを含む公開ツールと注意事項を確認し、**作成 → 接続**します。
7. 新しいチャットの **＋** から Poyto を検索して選択します。

同じ Tunnel を移行した場合は既存接続の **更新する／Refresh** でメタデータを更新し、新しいチャットで確認します。新しい Tunnel ならその ID で新規登録します。ローカルの Codex プラグインをコピーするだけでは Web 登録は完了しません。

現行の公式説明では Developer mode は read/write の両方に対応します。機能はアカウントやワークスペースの設定に従います。シェルも書き込み可能なツールとして扱われます。

## 7. 接続先と実操作を確認

ChatGPT で次の順に依頼します。

1. 「Poyto の server_info で、接続先の操作ルートを確認して。」
2. 「Poyto の exec_command で poyto --help を実行して。」
3. 「許可ルートに poyto-smoke.txt を作り、connected と書いて read で読み戻して。このテストファイル作成を許可します。」
4. 「Poyto で残高と保有ポジションを確認して。」

表示されるルートが**移行先のもの**であることを確認します。上記は読み取りとテストファイル操作です。POYP の買い／売りを接続テストとして実行する必要はありません。実際の変更操作にはユーザーの指示に加え、専用 MCP ツールの `confirm=true`、CLI の `--yes` を使用します。

## 8. 停止・更新・再起動

```bash
tunnel-client runtimes stop poyto
```

再開は第5節の `runtimes connect` を再実行します。ソース更新時は停止後に次を実行して再開します。

```bash
cd "$poyto_repo"
git pull --ff-only
.venv/bin/python -m pip install -e '.[agent]'
```

未コミットの変更は保持してから更新してください。ツール定義を変えたら ChatGPT 側も Refresh します。サーバー再起動後は古い `write_stdin` のセッション ID は使えません。

### OS 起動時にも動かす場合（systemd）

第5節でプロファイル生成と接続に成功した後、managed runtime を停止し、**同じ Linux ユーザー**の systemd サービスとして起動します。両方を同時起動しません。以下は上記インストール先を使うテンプレートです。

```bash
tunnel-client runtimes stop poyto
mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/poyto-tunnel.service" <<'UNIT'
[Unit]
Description=Poyto Secure MCP Tunnel

[Service]
Type=simple
ExecStart=%h/.local/bin/tunnel-client run --profile-dir %h/.config/tunnel-client --profile poyto
Restart=on-failure
RestartSec=5
UMask=0077

[Install]
WantedBy=default.target
UNIT
systemctl --user daemon-reload
systemctl --user enable --now poyto-tunnel.service
systemctl --user status poyto-tunnel.service
```

`XDG_CONFIG_HOME` を変更している場合はユニット配置先と `--profile-dir` を実際の設定先に合わせます。ログイン前・ログアウト後も動かすサーバーでは、管理者が対象ユーザーの linger を有効にします。

```bash
sudo loginctl enable-linger "$(id -un)"
```

systemd を選んだ後の操作は `runtimes connect/stop` ではなく以下を使います。

```bash
systemctl --user restart poyto-tunnel.service
systemctl --user stop poyto-tunnel.service
journalctl --user -u poyto-tunnel.service -n 50
```

systemd テンプレートは移行先での有効化と再起動テストが必要です。サービスが active でも接続成功とは限りません。起動ログに示されるループバックの `/readyz` と、ChatGPT の `server_info` で確認します。

## Docker で動かす場合

Linux 上で Docker Engine と `!reset` を扱える Compose を使用します。Python の直接起動の代わりに、移行先のチェックアウトで実行します。

```bash
docker compose -f compose.yaml -f compose.secure-tunnel.yaml up -d --build
```

Poyto は `127.0.0.1:8765/mcp` で待機します。Tunnel クライアントは**同じ Linux ホスト**で動かします。シェルは Poyto コンテナー内で動くため、ホストの `/home/...` とコンテナー内の `/workspace/Poyto` を区別してください。

初回セットアップでは JSON セッションを永続ボリュームへ配置します。

```bash
docker compose cp /absolute/private/path/session.json poyto:/data/session.json
docker compose exec -u 0 poyto chown 10001:10001 /data/session.json
docker compose exec -u 0 poyto chmod 600 /data/session.json
docker compose exec poyto poyto balances
```

既存セッションの差し替え時は、更新が競合しないよう利用中のクライアントを停止して作業します。第4・5節の Tunnel ID、キー、tunnel-client を用意し、stdio 用接続の代わりに実行します。

```bash
tunnel-client runtimes connect \
  --alias poyto --profile poyto \
  --tunnel-id "$poyto_tunnel_id" \
  --runtime-api-key "file:$poyto_key_file" \
  --mcp-server-url http://127.0.0.1:8765/mcp
tunnel-client runtimes status poyto --json
```

ChatGPT 登録と確認は第6・7節と共通です。`POYTO_PLUGIN_TUNNEL_PORT` を変える場合は Compose 起動時と `--mcp-server-url` のポートを揃えます。Docker の再起動ポリシーとは別に tunnel-client の自動起動も設定してください。

## トラブルシューティング

| 状況 | 確認・対処 |
| --- | --- |
| `poyto: command not found` | `.venv` に `.[agent]` が入っているか確認。stdio は `run-plugin-stdio.sh` 経由で起動し、変更後は Tunnel/Poyto プロセスを再起動する。 |
| Tunnel が ChatGPT に出ない | 対象ワークスペースへの関連付け、使用者の Read + Use 権限を確認する。 |
| `healthy` だが `ready` でない／検出失敗 | キーの権限、Tunnel ID、外向き HTTPS、MCP の起動パスとログを確認する。 |
| POYP の認証失敗 | セッションパス、読み書き権限、refresh token の有効性、別の token 環境変数で上書きされていないかを確認する。 |
| 操作先が旧マシンになる | 旧クライアントを止めるか移行先専用の Tunnel を作る。同じ Tunnel を複数ホストで同時稼働させない。 |
| 更新したツールが出ない | サーバー再起動、ChatGPT の Refresh、新しいチャットで再確認する。 |
| ファイルルート外エラー | `server_info` で移行先のルートを確認し、必要なら `POYTO_PLUGIN_ROOTS` を設定して再起動する。 |

CLI の詳細は[CLI](cli.md)、検証済み範囲は[ChatGPT Web](chatgpt-web.md)を参照してください。OpenAI 側の現行仕様は [Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels) と [Developer mode](https://developers.openai.com/api/docs/guides/developer-mode)が基準です。
