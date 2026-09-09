# Poyto Portainer 導入ガイド（amd64 / arm64・日本語）

この手順は **64bit Linux + Portainer（Docker Standalone）** 用です。amd64（x64）と arm64 でセットアップ手順は共通で、CPU に対応する Stack YAML を選びます。Portainer の管理画面を開く PC ではなく、デプロイ先 Environment の CPU を確認してください。Swarm 用ではありません。

サーバー 上で Poyto と公式 tunnel-client の2コンテナーを動かします。ChatGPT 自体を サーバー で動かすわけではありません。ソースのビルドやホストへの Python/venv インストールは不要です。

```text
ChatGPT Web → Secure MCP Tunnel → サーバー の tunnel コンテナー
           → サーバー の poyto コンテナー → POYP
```

## 入力する3種類の情報

| 情報 | 形式・内容 | 入れる場所 |
| --- | --- | --- |
| Tunnel ID | `tunnel_...` | Portainer の `POYTO_TUNNEL_ID`、または YAML の `--control-plane.tunnel-id=` |
| OpenAI API キー（Tunnel 用キー） | `sk-proj-...` など。Tunnels の Read・Use 権限が必要 | サーバー の `/opt/poyto/secrets/runtime.key` |
| POYP セッション | access/refresh token を含むセッション JSON | サーバー の `/opt/poyto/data/session.json` |

**「Tunnel 用キー」は OpenAI API キーのことです。Tunnel ID や POYP の token とは別です。**
`runtime.key` の中身はキーだけを1行で保存します。`API_KEY=` や引用符は付けません。
このガイドの ID は置き換え用の例です。実際の API キー・個人の Tunnel ID は記載していません。

## 1. デプロイ先の CPU を確認して YAML を選ぶ

Docker を実行するサーバーに SSH して実行します。

```bash
uname -m
getconf LONG_BIT
docker info --format '{{.Architecture}}'
```

| CPU | 表示例 | 使用する Stack YAML |
| --- | --- | --- |
| amd64（x64 / x86_64） | `x86_64`、`amd64` | [amd64 用](../compose.portainer.amd64.yaml) |
| arm64（AArch64） | `aarch64`、`arm64` | [arm64 用](../compose.portainer.arm64.yaml) |

OS も64bit（`getconf LONG_BIT` が `64`）を使用します。各 YAML は両コンテナーに
`platform: linux/amd64` または `platform: linux/arm64` を明示しています。
公開イメージは両 CPU に対応しており、手元でのビルドは不要です。
32bit の `armv7l` / `armhf` はこの配布構成の対象外です。

CPU 自動選択の [共通 YAML](../compose.portainer.yaml) もありますが、以下では CPU ごとのファイルを使います。

## 2. サーバー 上に保存先を用意

Docker と Portainer の接続が済んでいる状態で、**サーバー の SSH ターミナル**から実行します。

```bash
sudo install -d -o 10001 -g 10001 -m 700 /opt/poyto/data /opt/poyto/secrets
sudo install -d -o 10001 -g 10001 -m 755 /opt/poyto/workspace
```

| サーバー 上の場所 | 用途 |
| --- | --- |
| `/opt/poyto/data/session.json` | POYP セッション。refresh 後もここへ保存する |
| `/opt/poyto/secrets/runtime.key` | OpenAI Tunnel 実行用キー |
| `/opt/poyto/workspace` | ChatGPT に読み書きさせる作業フォルダー |

`10001` は Poyto コンテナーの実行 UID/GID です。セッションはファイルだけでなく**ディレクトリごと**書き込み可能にマウントします。refresh 時のファイル置換に必要です。

## 3. POYP セッションを サーバー に転送

利用を許可された最新のセッション JSON を SCP などで サーバー へ転送します。例えば手元の PC から：

```bash
scp /path/to/android-session.json USER@SERVER_IP:~/poyto-session-transfer.json
```

`USER` と `SERVER_IP` は サーバー の SSH ユーザー／アドレスに置き換えます。その後 サーバー で：

```bash
sudo install -o 10001 -g 10001 -m 600 "$HOME/poyto-session-transfer.json" /opt/poyto/data/session.json
rm -- "$HOME/poyto-session-transfer.json"
```

旧環境で同じセッションを使っている処理を止めてから最新ファイルを移します。同じ refresh token を複数環境で並行利用しないでください。セッションの中身を Portainer の YAML や ChatGPT に貼る必要はありません。

初期セッションがまだない場合は、[認証手順](authentication.md)に従って取得してください。

## 4. Tunnel とキーを用意

[OpenAI Platform → Tunnels](https://platform.openai.com/settings/organization/tunnels) で サーバー 用の Tunnel を作り、利用する ChatGPT ワークスペースを関連付けます。作成・編集には **Read + Manage**、実行用キーには **Read + Use** の Tunnel 権限が必要です。

既存の Tunnel ID を引き継ぐ場合は旧環境の tunnel-client を停止してから サーバー を起動します。旧環境も残す場合は サーバー 用に別の Tunnel を作ってください。既存の managed runtime なら停止は旧環境で `tunnel-client runtimes stop poyto` です。

[API キー設定](https://platform.openai.com/settings/organization/api-keys)で用意した実行用キーを サーバー のファイルへ保存します。以下は初期設定用です。既存キーを差し替える場合は、使用中の Tunnel を止めてから行います。

```bash
sudo -v
read -rsp 'OpenAI Tunnel runtime key: ' poyto_runtime_key
printf '\n'
if [ -n "$poyto_runtime_key" ]; then
  printf '%s\n' "$poyto_runtime_key" | sudo tee /opt/poyto/secrets/runtime.key >/dev/null
  sudo chown 10001:10001 /opt/poyto/secrets/runtime.key
  sudo chmod 600 /opt/poyto/secrets/runtime.key
fi
unset poyto_runtime_key
sudo test -s /opt/poyto/secrets/runtime.key
```

キー本体は Stack の環境変数に入れません。tunnel コンテナーだけが私有ファイルを読みます。

## 5. Portainer で Stack を作成

1. サーバー の **Environment** を選択。
2. **Stacks → Add stack → Web editor**。
3. Stack 名を `poyto` にする。
4. 第1節で選んだ **amd64 用または arm64 用の YAML** を全部貼り付ける。以下にも全文を掲載しています。
5. **Environment variables** に1つ追加する。

   | Name | Value |
   | --- | --- |
   | `POYTO_TUNNEL_ID` | 自分の `tunnel_...` |

6. **Deploy the stack** を押す。

### amd64（x64）用 Stack YAML

[compose.portainer.amd64.yaml](../compose.portainer.amd64.yaml) と同じ内容です。

```yaml
# Portainer Docker Standalone on Linux/amd64.
# Prepare /opt/poyto/{data,workspace,secrets} on the Docker host first.
services:
  poyto:
    platform: linux/amd64
    image: ghcr.io/tqmane/poyto:latest
    init: true
    restart: unless-stopped
    command: ["poyto-plugin", "--host", "127.0.0.1", "--port", "8765", "--insecure-no-auth"]
    environment:
      POYTO_PLUGIN_PORT: "8765"
      POYTO_PLUGIN_ROOTS: /workspace:/data
      POYTO_PLUGIN_EXEC_MODE: container
      POYTO_SESSION_FILE: /data/session.json
    volumes:
      - /opt/poyto/data:/data
      - /opt/poyto/workspace:/workspace
    healthcheck:
      test: ["CMD", "python", "-c", "import socket; socket.create_connection(('127.0.0.1',8765),2).close()"]
      interval: 30s
      timeout: 5s
      start_period: 30s
      retries: 3

  tunnel:
    platform: linux/amd64
    image: ghcr.io/openai/tunnel-client:v0.0.14
    user: "10001:10001"
    restart: unless-stopped
    # Share only Poyto's network namespace: localhost reaches its private MCP.
    network_mode: service:poyto
    depends_on:
      poyto:
        condition: service_healthy
    command:
      - --control-plane.api-key=file:/run/poyto-secrets/runtime.key
      - --control-plane.tunnel-id=${POYTO_TUNNEL_ID:?Set POYTO_TUNNEL_ID in Portainer}
      - --mcp.server-url=http://127.0.0.1:8765/mcp
      - --health.listen-addr=127.0.0.1:8080
    volumes:
      - /opt/poyto/secrets:/run/poyto-secrets:ro
```

### arm64 用 Stack YAML

[compose.portainer.arm64.yaml](../compose.portainer.arm64.yaml) と同じ内容です。

```yaml
# Portainer Docker Standalone on Linux/arm64.
# Prepare /opt/poyto/{data,workspace,secrets} on the Docker host first.
services:
  poyto:
    platform: linux/arm64
    image: ghcr.io/tqmane/poyto:latest
    init: true
    restart: unless-stopped
    command: ["poyto-plugin", "--host", "127.0.0.1", "--port", "8765", "--insecure-no-auth"]
    environment:
      POYTO_PLUGIN_PORT: "8765"
      POYTO_PLUGIN_ROOTS: /workspace:/data
      POYTO_PLUGIN_EXEC_MODE: container
      POYTO_SESSION_FILE: /data/session.json
    volumes:
      - /opt/poyto/data:/data
      - /opt/poyto/workspace:/workspace
    healthcheck:
      test: ["CMD", "python", "-c", "import socket; socket.create_connection(('127.0.0.1',8765),2).close()"]
      interval: 30s
      timeout: 5s
      start_period: 30s
      retries: 3

  tunnel:
    platform: linux/arm64
    image: ghcr.io/openai/tunnel-client:v0.0.14
    user: "10001:10001"
    restart: unless-stopped
    # Share only Poyto's network namespace: localhost reaches its private MCP.
    network_mode: service:poyto
    depends_on:
      poyto:
        condition: service_healthy
    command:
      - --control-plane.api-key=file:/run/poyto-secrets/runtime.key
      - --control-plane.tunnel-id=${POYTO_TUNNEL_ID:?Set POYTO_TUNNEL_ID in Portainer}
      - --mcp.server-url=http://127.0.0.1:8765/mcp
      - --health.listen-addr=127.0.0.1:8080
    volumes:
      - /opt/poyto/secrets:/run/poyto-secrets:ro
```

どちらか一方だけをデプロイしてください。保存先、API キー、Tunnel ID の設定方法は共通です。

### Tunnel ID を直接書く場合

環境変数を使う代わりに、次の行を置き換えても構いません。

```yaml
- --control-plane.tunnel-id=${POYTO_TUNNEL_ID:?Set POYTO_TUNNEL_ID in Portainer}
```

置き換え後（`tunnel_YOUR_ID` を自分の ID に変更）：

```yaml
- --control-plane.tunnel-id=tunnel_YOUR_ID
```

この場合、Portainer の `POYTO_TUNNEL_ID` 環境変数は不要です。
API キーをこの行へ入れてはいけません。API キーは `runtime.key` に保存します。

### 配置とネットワーク

`build:` や `./` マウント、複数 Compose ファイルの指定は不要です。絶対パスは Portainer 管理 PC ではなく、Docker を実行する サーバー 上のものです。

この Stack はホストへポートを公開しません。tunnel は poyto のネットワーク名前空間を共有し、`127.0.0.1:8765` へ接続します。ChatGPT からの入口は Secure MCP Tunnel です。ルーターのポート開放も不要です。

両サービスは `restart: unless-stopped` です。サーバー 起動時に Docker デーモンが起動する設定なら再起動後も復帰します。手動停止したコンテナーは自動再開しません。

## 6. 起動を確認

Portainer の Stack 画面で：

- `poyto` が **healthy** になる。
- `tunnel` のログで接続エラーが繰り返されていないか確認する。
- `poyto` コンテナーの **Console** を通常の実行ユーザー（UID `10001`）で開き、以下を実行する。root での成功だけでは通常稼働時の権限を確認できません。

```bash
id
touch /data/.write-test && rm /data/.write-test
poyto --help
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8080/readyz', timeout=5).read().decode())"
poyto balances
```

`readyz` は tunnel と共有したネットワーク経由で確認します。残高取得が成功すれば POYP セッションも有効です。コンテナーの running 表示だけでは接続成功とは判断しません。

## 7. ChatGPT Web に登録して使う

1. **設定 → セキュリティとログイン → Developer mode** を有効化。
2. [プラグイン](https://chatgpt.com/plugins)の **＋／アプリを作成**。
3. 名前は `Poyto Server Control` など、接続先を区別できるものにする。
4. 接続は **トンネル**、ID は第4節で用意したものを選択。
5. MCP の認証は **認証なし**。トンネル側がアクセスを認証する。
6. ツールと注意事項を確認して **作成 → 接続**。
7. 新しいチャットで **＋ → Poyto Server Control** を選ぶ。

同じ Tunnel を引き継いだ場合は既存接続を Refresh して新しいチャットで確認します。

最初は次の依頼で接続確認します。

> Poyto の server_info と poyto --help を実行して。続けて /workspace/poyto-smoke.txt に connected と書き、読み戻して。このテストファイル作成を許可します。

サーバー の `/opt/poyto/workspace/poyto-smoke.txt` にファイルができます。次に「残高と保有ポジションを確認して」と依頼できます。

シェルは**コンテナー内**で動きます。この Stack は サーバー ホスト全体の管理権限や Docker ソケットを渡しません。ホストのプロジェクトを扱う場合は、そのフォルダーだけを追加マウントしてください。

## 8. 実際に発生した権限エラーと直し方

今回のセットアップでは、プラグインには接続できていましたが、`health` の実行時に以下のエラーが出ました。

```text
Permission denied: '/data/session.json.tmp'
```

Poyto はセッション更新時に、一時ファイル `session.json.tmp` を作ってから `session.json` に置き換えます。このため、**セッションファイルと `/data` ディレクトリの両方**へ書き込める必要があります。`health` でもクライアント初期化時の自動 refresh によってセッション保存が発生する場合があります。

### サーバー の SSH ターミナルで修正

```bash
sudo chown -R 10001:10001 /opt/poyto/data
sudo chmod 700 /opt/poyto/data
sudo chmod 600 /opt/poyto/data/session.json
```

これは Poyto 専用データフォルダーに対するコマンドです。マウント元を変更している場合は、`/opt/poyto/data` を**実際に `/data` に対応する サーバー 側のパス**に置き換えます。`chmod 777` や root 常用への変更は必要ありません。

### Portainer の Console で再確認

`poyto` コンテナーの通常ユーザーで実行します。

```bash
id
touch /data/.write-test && rm /data/.write-test
poyto balances
```

`id` で `uid=10001` を確認し、一時ファイルの作成・削除と残高取得が成功すれば修正完了です。通常、所有者・権限の変更だけならコンテナーの再起動は不要です。その後 ChatGPT からも再度依頼します。

今回、上記の権限修正後にユーザーから「できた」との動作成功報告がありました。これはユーザーによる確認であり、こちらでの実機負荷試験・再起動試験とは区別しています。

## 9. 更新とその他のトラブル対処

- 更新は Portainer でイメージを再取得し、Stack 全体を再デプロイします。ネットワークを共有しているため、Poyto のコンテナーを再作成したときは tunnel も再作成します。
- 更新後は ChatGPT の接続を Refresh。データ・セッション・キーは `/opt/poyto` に残ります。
- `no matching manifest`：32bit OS／Docker でないかを確認。
- `permission denied`：第8節の所有者・権限修正を実施。残る場合は `/data` が読み取り専用（`:ro`）になっていないかも確認。
- `unauthorized`／`forbidden`：Tunnel キーの権限と ID を確認。POYP 認証エラーならセッションの有効性を確認。
- ローカルに Docker の `poyto` が起動しただけでは、Tunnel や ChatGPT の接続はまだ完了していません。
- 同じ Tunnel に旧環境が接続していないか確認。想定外の操作先になる場合は別の Tunnel を作る。

この Stack の Compose 設定と配布イメージの amd64 / arm64 マニフェストを確認しています。ユーザーから権限修正後の動作成功報告がありますが、負荷・長時間稼働・再起動後の復帰は移行先で別途確認してください。

参考：[Portainer Stack 作成](https://docs.portainer.io/user/docker/stacks/add)、[OpenAI Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)、[公式 tunnel-client Docker 配布](https://github.com/openai/tunnel-client/blob/main/docs/deployment/docker.md)。
