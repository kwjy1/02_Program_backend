import os
import toml
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta

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

# Set the date range for news articles
start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
end_date = datetime.now().strftime("%Y-%m-%d")

def get_kor_query(query_kor, days=1, display=100, sort='sim'):
    naver_url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": api_key_naver_client_id,
        "X-Naver-Client-Secret": api_key_naver_client_secret
    }
    params = {
        "query": query_kor,
        "display": display,
        "start": 1,
        "sort": sort
    }
    response = requests.get(naver_url, headers=headers, params=params).json().get("items", [])
    unique = {it["link"]: it for it in response}.values()

    now_utc = datetime.now(timezone.utc)
    recent_naver = [
        it for it in unique
        if 0 <= (now_utc - datetime.strptime(it["pubDate"], "%a, %d %b %Y %H:%M:%S %z").astimezone(timezone.utc)).total_seconds() <= days * 24 * 3600
    ]
    return len(recent_naver), recent_naver

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

system_context = """
You are an expert assistant for National Strategy Technology policy, you will carefully read them and produce a concise summary.
"""

techs = pd.read_csv("tech_preset.csv", index_col=0)

for query_kor, query_eng, desc in zip(techs['query_kor'], techs['query_eng'], techs['description']):
    print(f"Processing: {query_kor} / {query_eng}")
    number_of_article_kor, article_kor = get_kor_query(query_kor, days=1, display=100, sort='sim')
    number_of_article_eng, article_eng = get_eng_query(query_eng, start_date=start_date, end_date=end_date)

    articles_text = ""
    for i, article in enumerate(article_kor, 1):
        # print(type(article))
        # print(article['link'])
        articles_text += (
            f"{i}. Title: {article['title'].replace('[', '').replace(']', '')}\n"
            f"   Description: {article['description']}\n"
            f"   URL: {article['link']}\n\n"
        )
        count = i

    for i, article in enumerate(article_eng, count):
        articles_text += (
            f"{i}. Title: {article['title'].replace('[', '').replace(']', '')}\n"
            f"   Description: {article['description']}\n"
            f"   URL: {article['url']}\n\n"
        )

    prompt = f"""
Group the news articles below into 2~5 major issues (depending on the number of articles) and summarize each issue.
Issues should be distinct and not overlap.
Use a mix of Korean and international news

0. Be written in KOREAN
1. Topic Title: 10-20 words.
2. Summary: 4-5 sentence overview of the core theme and some specific content that article says.
3. Articles: Markdown list of titles with URLs. 

Format MUST BE EXACTLY like this Markdown template:

## Topic 1: <Topic Title>
**Summary:** ... \n
**Articles:**
- [Title A](URL) \n
- [Title B](URL) \n

## Topic 2: <Topic Title>
**Summary:** ... \n
**Articles:**
- [Title C](URL) \n
- [Title D](URL) \n

From here on, you will only use the articles below to summarize.
Articles:
{articles_text}

They are news articles related to {desc}. So you MUST exclude not related to {desc} or unnecessary, or duplicated articles.
For each topics, Articles SHOULD NOT be too many, just 3~5 articles per topic.
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

    html_body = markdown.markdown(response.choices[0].message.content.strip(), extensions=['nl2br'])
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