import requests
import pandas as pd
import json
import toml
from typing import List

class AligoSMS:
    def __init__(self, api_key: str, user_id: str, sender: str):
        self.api_key = api_key
        self.user_id = user_id
        self.sender = sender
        self.base_url = "https://apis.aligo.in/send/"

    def send_sms(self, receivers: List[str], message: str, testmode: bool = False) -> dict:
        """
        Send SMS to multiple receivers
        """
        data = {
            "key": self.api_key,
            "user_id": self.user_id,
            "sender": self.sender,
            "receiver": ",".join(receivers),
            "msg": message,
            "testmode_yn": "Y" if testmode else "N"
        }
        
        print(data)

        response = requests.post(self.base_url, data=data)
        return response.json()

def main():
    with open("secret_keys.toml", "r", encoding="utf-8") as f:
        secrets = toml.load(f)
    # ALIGO API credentials - Replace these with your actual credentials
    API_KEY = secrets["aligo_api_key"]
    USER_ID = secrets['aligo_user_id']
    SENDER = secrets['aligo_sender']  # Must be registered in ALIGO

    # Initialize SMS sender
    sms_sender = AligoSMS(API_KEY, USER_ID, SENDER)

    # Read phone numbers from CSV
    try:
        df = pd.read_csv('receiverList.csv', dtype={'phone': str})  # 전화번호를 문자열로 읽기
        phone_numbers = df['phone'].tolist()
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    # Sample message - Replace this with your actual message
    message = "안녕하세요! 테스트 메시지입니다."

    # Send SMS
    try:
        result = sms_sender.send_sms(phone_numbers, message, testmode=True)  # Set testmode=False for actual sending
        print("SMS sending result:", json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error sending SMS: {e}")

if __name__ == "__main__":
    main()
