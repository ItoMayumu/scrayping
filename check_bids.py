import requests
import json
import os

JSON_FILE = "/home/runner/work/scrayping/scrayping/data.json"
# 正しいログインURL
LOGIN_URL = "https://api.torakuru.net/V0/login"
DATA_URL = "https://api.torakuru.net/V0/protected/admin/getShipmentsWithoutBids?page=1&limit=10"

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL = "G4CKCNBAS"  # 送信先の Slack チャンネル（適宜変更）

def send_to_slack(message):
    if not SLACK_BOT_TOKEN:
        print("SLACK_BOT_TOKEN が設定されていません")
        return
    
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "channel": SLACK_CHANNEL,
        "text": message
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.ok:
        print("Slack に通知しました")
    else:
        print(f"Slack 送信エラー: {response.text}")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0",
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://demo.torakuru.net",
    "Referer": "https://demo.torakuru.net/",
    "Connection": "keep-alive"
}

# ログインデータ
credentials = {
    "emailAddress": "admin@gmail.com",
    "password": "axross_3760",
    "roleID": 3
}

# セッションを作成
session = requests.Session()

# 1. ログインリクエスト
login_response = session.post(LOGIN_URL, json=credentials, headers=headers)

# 2. ログイン成功の確認
if login_response.ok:
    print("ログイン成功")

    # 3. ログインレスポンスを確認
    login_data = login_response.json()
    print("ログインレスポンス:", login_data)

    # 4. 認証トークンを取得
    token = login_data.get("token")
    if not token:
        print("認証トークンが取得できませんでした")
        exit()

    # 5. 認証ヘッダーを追加
    headers["Authorization"] = f"Bearer {token}"
    print(f"送信ヘッダー: {headers}")

    # 6. データ取得リクエスト
    data_response = session.get(DATA_URL, headers=headers)

    # 7. データ取得成功の確認
    print(f"データ取得ステータスコード: {data_response.status_code}")

    if data_response.ok:
        print("データ取得成功")

        try:
            # JSON に変換
            data_json = data_response.json()
            print("取得した JSON データ:", data_json)

            # shipmentId を抽出
            shipment_ids = [
                record["shipmentId"]
                for record in data_json.get("records", [])
                if "shipmentId" in record and record["shipmentId"] is not None
            ]

            # 結果を表示
            if shipment_ids:
                print("取得した shipmentId:")
                print(shipment_ids)

                # 既存の JSON データを読み込む
                if os.path.exists(JSON_FILE):
                    with open(JSON_FILE, "r", encoding="utf-8") as file:
                        try:
                            existing_data = json.load(file)
                            if not isinstance(existing_data, list):
                                existing_data = []  # リストでない場合は空リストにする
                        except json.JSONDecodeError:
                            existing_data = []  # JSON 解析エラーの場合は空リストにする
                else:
                    existing_data = []

                # 既に存在する shipmentId をチェック
                new_shipment_ids = []
                duplicate_shipment_ids = []
                
                for shipment_id in shipment_ids:
                    if shipment_id in existing_data:
                        duplicate_shipment_ids.append(shipment_id)
                    else:
                        new_shipment_ids.append(shipment_id)
                
                if duplicate_shipment_ids:
                    print(f"既に存在する shipmentId: {duplicate_shipment_ids}")
                
                if new_shipment_ids:
                    print(f"新しく追加する shipmentId: {new_shipment_ids}")

                    # 新しい shipmentId を追加
                    updated_shipment_ids = existing_data + new_shipment_ids

                    # JSON ファイルに保存
                    with open(JSON_FILE, "w", encoding="utf-8") as file:
                        json.dump(updated_shipment_ids, file, ensure_ascii=False, indent=4)

                    print(f"{JSON_FILE} に保存しました")
                    
                    message = f"(test)新しい荷物が追加されました: {new_shipment_ids}"
                    send_to_slack(message)
            else:
                print("shipmentId が見つかりませんでした")

        except Exception as e:
            print("JSON の解析に失敗しました")
            print(data_response.text)

    else:
        print(f"データ取得失敗: {data_response.status_code}")
        print(data_response.text)

else:
    print("ログイン失敗")
    print(f"ステータスコード: {login_response.status_code}")
    print(f"レスポンス: {login_response.text}")
