import toml
import requests
from datetime import datetime, timezone, timedelta

import openai
from newsapi import NewsApiClient


with open("secret_keys.toml", "r", encoding="utf-8") as f:
    secrets = toml.load(f)

openai.api_key = secrets["api_key_openai"]
api_key_newsapi = secrets["api_key_newsapi"]
api_key_naver_client_id = secrets["api_key_naver_client_id"]
api_key_naver_client_secret = secrets["api_key_naver_client_secret"]

presets = {
    "AI": ("AI", "AI"),
    "반도체": ("반도체", "Semiconductor"),
    "NPU": ("NPU", "NPU"),
    "디스플레이": ("디스플레이", "Display"),
    "이차전지": ("이차전지", "Secondary Battery"),
    "자율주행": ("자율주행", "Autunomous Driving"),
    "전기차": ("전기차 ", "EV"),
    "차세대원자력": ("원자력", "Nuclear Energy"),
    "바이오": ("바이오", "Biotechnology"),
    "수소": ("수소", "Hydrogen"),
    "SMR": ("SMR", "SMR"),
    "사이버보안": ("사이버보안", "Cybersecurity"),
    "6G": ("6G", "6G"),
    "로봇": ("로봇", "Robotics"),
    "양자": ("양자", "Quantum"),
    "기후변화": ("기후변화", "Climate Change"),
}

# Set the date range for news articles
start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
end_date = datetime.now().strftime("%Y-%m-%d")

def get_kor_query(query_kor, days=1, display=100, sort='sim'):
    naver_url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": api_key_naver_client_id,
        "X-Naver-Client-Secret":api_key_naver_client_secret
    }
    params = {
        "query": query_kor,
        "display": display,
        "start": 1,
        "sort": sort
    }
    response = requests.get(naver_url, headers=headers, params=params).json().get("items", [])
    
    # Remove duplicates based on the link
    unique = {it["link"]: it for it in response}.values()

    now_utc = datetime.now(timezone.utc)
    recent_naver = [
        it for it in unique
        if (datetime.strptime(it["pubDate"], "%a, %d %b %Y %H:%M:%S %z").astimezone(timezone.utc) - now_utc).total_seconds() <= days * 24 * 3600
    ]

    return len(recent_naver) , recent_naver

def get_eng_query(query_eng, start_date=start_date, end_date=end_date):
    newasapi = NewsApiClient(api_key=api_key_newsapi)

    params = {
        "q": query_eng,
        "from_param": start_date,
        "to": end_date,
        "pageSize": 100,
    }

    articles = newasapi.get_everything(**params)
    number_of_articles = articles["totalResults"]
        
    return number_of_articles, articles["articles"]



for query in presets:
    query_kor, query_eng = presets[query]

    get_kor_query(query_kor, days=1, display=100, sort='sim')