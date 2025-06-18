import os
import toml
import requests
from datetime import datetime, timezone, timedelta
import boto3
from botocore.exceptions import ClientError

import openai
from newsapi import NewsApiClient
import markdown


with open("secret_keys.toml", "r", encoding="utf-8") as f:
    secrets = toml.load(f)

output_dir = "output_html"
os.makedirs(output_dir, exist_ok=True)

openai.api_key = secrets["api_key_openai"]
api_key_newsapi = secrets["api_key_newsapi"]
api_key_naver_client_id = secrets["api_key_naver_client_id"]
api_key_naver_client_secret = secrets["api_key_naver_client_secret"]

# 바이오, 우주항공해양, 모빌리티, 차세대통신 가르마

presets = {
    "AI": ("AI", "AI"),
    "반도체": ("반도체", "Semiconductor"),
    "디스플레이": ("디스플레이", "Display"),
    "이차전지": ("이차전지", "Secondary Battery"),
    "자율주행": ("자율주행", "Autonomous Driving"),
    "전기차": ("전기차", "EV"),
    "UAM": ("UAM", "UAM"),
    "차세대원자력": ("원자력", "Nuclear Energy"),
    "바이오": ("바이오", "Biotechnology"),
    "의약품": ("의약품", "Pharmaceuticals"),
    "디지털헬스": ("디지털 헬스", "Digital Health"),
    "수소": ("수소", "Hydrogen"),
    "사이버보안": ("사이버보안", "Cybersecurity"),
    "6G": ("6G", "6G"),
    "로봇": ("로봇", "Robotics"),
    "양자": ("양자", "Quantum"),
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
        "page_size": 100,
    }

    articles = newasapi.get_everything(**params)
    number_of_articles = articles["totalResults"]
        
    return number_of_articles, articles["articles"]


index_html = """
<html>
<head>
    <meta charset="utf-8">
    <title>기술별 뉴스 요약</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="container py-4">
    <h1 class="mb-4">기술별 뉴스 요약</h1>
    <ul class="list-group">
"""

system_context = """
You are an expert assistant for National Strategy Technology policy, you will carefully read them and produce a concise summary.
"""

for tech, (_, query_eng) in presets.items():
    index_html += f'<li class="list-group-item"><a href="{query_eng}.html">{tech} ({query_eng})</a></li>\n'

index_html += """
    </ul>
</body>
</html>
"""

with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
    f.write(index_html)

for query_kor, query_eng in presets.values():
    print(f"Processing: {query_kor} / {query_eng}")
    number_of_article_kor, article_kor = get_kor_query(query_kor, days=1, display=100, sort='sim')
    number_of_article_eng, article_eng = get_eng_query(query_eng, start_date=start_date, end_date=end_date)

    articles_text = ""
    for i, article in enumerate(article_kor, 1):
        # print(type(article))
        # print(article['link'])
        articles_text += (
            f"{i}. Title: {article['title']}\n"
            f"   Description: {article['description']}\n"
            f"   URL: {article['link']}\n\n"
        )
        count = i

    for i, article in enumerate(article_eng, count):
        articles_text += (
            f"{i}. Title: {article['title']}\n"
            f"   Description: {article['description']}\n"
            f"   URL: {article['url']}\n\n"
        )

    prompt = f"""
Group the news articles below into 3~5 major issues (depending on the number of articles) and summarize each issue.
Use a mix of Korean and international news, and you can exclude unnecessary articles.

0. Be written in KOREAN
1. **Topic Title**: 10-20 words.
2. **Summary**: 4-5 sentence overview of the core theme and some specific content that article says.
3. **Articles**: Markdown list of titles with URLs. and remove duplicate(or similar) articles

Format exactly like this:

## Topic 1: <Topic Title>
**Summary:** ... \n
**Articles:**
- [Title A](URL) \n
- [Title B](URL) \n

Articles:
{articles_text}
"""
 
    response = openai.ChatCompletion.create(
        model = "gpt-4.1",
        messages = [{"role": "system", "content": system_context},
                    {"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=32768,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        response_format={
            "type": "text"
        }
    )

    result = {}
    result['query_eng'] = markdown_content = response.choices[0].message.content.strip()

    html_body = markdown.markdown(markdown_content, extensions=['nl2br'])
    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>{query_eng} 뉴스 요약</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="container py-4">
        <h1 class="mb-4">{query_eng} 뉴스 요약</h1>
        <a href="index.html" class="btn btn-secondary mb-3">← 메인으로</a>
        <div class="card p-4">{html_body}</div>
    </body>
    </html>
    """
    with open(os.path.join(output_dir, f"{query_eng}.html"), "w", encoding="utf-8") as f:
        f.write(html)

def upload_to_s3(local_directory, bucket_name, s3_prefix=''):
    """
    Upload a directory to S3 bucket
    """
    s3_client = boto3.client('s3')
    
    for root, dirs, files in os.walk(local_directory):
        for filename in files:
            local_path = os.path.join(root, filename)
            relative_path = os.path.relpath(local_path, local_directory)
            s3_path = os.path.join(s3_prefix, relative_path)
            
            try:
                s3_client.upload_file(local_path, bucket_name, s3_path)
                print(f"Uploaded {local_path} to s3://{bucket_name}/{s3_path}")
            except ClientError as e:
                print(f"Error uploading {local_path}: {e}")


upload_to_s3(output_dir, 'tech-news-summary')