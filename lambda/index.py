# lambda/index.py
import json
import os
import requests  # HTTPリクエスト用
import re

# FastAPI エンドポイントURL（Colab + ngrokで公開されたURLに差し替えてください）
FASTAPI_URL = os.environ.get("FASTAPI_URL", "https://8aaa-34-16-118-76.ngrok-free.app")

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))
        
        # Cognitoで認証されたユーザー情報を取得
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")
        
        # リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])
        
        print("Processing message:", message)
        
        # 会話履歴にユーザーメッセージを追加
        messages = conversation_history.copy()
        messages.append({
            "role": "user",
            "content": message
        })
        
        # FastAPIに送信するペイロード
        fastapi_payload = {
            "message": message,
            "conversationHistory": conversation_history
        }

        print("Sending request to FastAPI server:", json.dumps(fastapi_payload))

        # FastAPI サーバーにPOSTリクエストを送信
        response = requests.post(FASTAPI_URL, json=fastapi_payload)
        response.raise_for_status()
        response_data = response.json()
        
        assistant_response = response_data.get("response", "")
        print("FastAPI response:", assistant_response)
        
        # 会話履歴にアシスタントの応答を追加
        messages.append({
            "role": "assistant",
            "content": assistant_response
        })
        
        # 成功レスポンスの返却
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": messages
            })
        }
        
    except Exception as error:
        print("Error:", str(error))
        
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }
