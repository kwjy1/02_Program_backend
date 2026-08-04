import os
import toml
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
import argparse

from openai import OpenAI
from newsapi import NewsApiClient
import markdown


with open("secret_keys.toml", "r", encoding="utf-8") as f:
    secrets = toml.load(f)

output_dir = "output_html"
os.makedirs(output_dir, exist_ok=True)

openai_client = OpenAI(api_key=secrets["api_key_openai"])
OPENAI_MODEL = "gpt-5.6-sol"
NEWSAPI_PAGE_SIZE = 100
NEWSAPI_MAX_PAGES = 2
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
    newsapi = NewsApiClient(api_key=api_key_newsapi)

    params = {
        "q": query_eng,
        "from_param": start_date,
        "to": end_date,
        "sort_by": "relevancy",
        "page_size": NEWSAPI_PAGE_SIZE,
    }

    first_page = newsapi.get_everything(**params, page=1)
    number_of_articles = first_page["totalResults"]
    collected_articles = list(first_page["articles"])

    if number_of_articles > NEWSAPI_PAGE_SIZE and NEWSAPI_MAX_PAGES >= 2:
        second_page = newsapi.get_everything(**params, page=2)
        collected_articles.extend(second_page["articles"])

    # Keep the first (most relevant) occurrence of duplicated URLs across pages.
    unique_articles = []
    seen_urls = set()
    for article in collected_articles:
        if article["url"] in seen_urls:
            continue
        seen_urls.add(article["url"])
        unique_articles.append(article)

    return number_of_articles, unique_articles

system_context = """
You are an expert assistant for National Strategy Technology policy, you will carefully read them and produce a concise summary.
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tech", type=str, default=None, help="콤마로 구분된 기술명(영문)만 처리 (예: AI,Display)")
    args = parser.parse_args()

    techs = pd.read_csv("tech_preset.csv", index_col=0)

    # --tech 인자가 있으면 해당 기술만 처리
    if args.tech:
        tech_list = [t.strip() for t in args.tech.split(",")]
        techs = techs[techs.index.isin(tech_list) | techs['query_eng'].isin(tech_list)]

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
        for i, article in enumerate(article_eng, len(article_kor) + 1):
            articles_text += (
                f"{i}. Title: {article['title'].replace('[', '').replace(']', '')}\n"
                f"   Description: {article['description']}\n"
                f"   URL: {article['url']}\n\n"
            )

        prompt = f"""
Select and summarize up to 5 concrete, newsworthy issues from the articles below.

Selection and grouping rules:
- First exclude articles that are unrelated to {desc}, duplicated, promotional, speculative without a concrete development, or too vague to identify what happened.
- Each topic MUST describe one specific event or tightly connected development, such as a named organization's announcement, a particular policy or regulatory action, a funding/deal, a product or research release, or a measurable incident.
- Group articles together only when they cover the same event or a direct follow-up to it. Sharing only a broad technology or industry category is NOT enough.
- Never create umbrella topics such as "AI industry trends", "recent technology developments", or a miscellaneous roundup.
- Do not force a fixed number of topics. Return only well-supported topics; omit weak leftover articles instead of merging unrelated stories.
- Topics must not overlap. Use Korean and international sources across the report when relevant, but never sacrifice topic specificity to create that mix.

Output requirements:
0. Write entirely in KOREAN.
1. Topic Title: identify the specific actor, action, and subject of the event in a concise title.
2. Summary: 4-5 sentences stating what happened, who did it, why it matters, and concrete facts reported by the cited articles. Avoid generic background statements.
3. Articles: include 2-5 of the most directly relevant, non-duplicated articles as a Markdown list of titles with URLs.

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

Use only the supplied articles. Do not invent facts, events, or URLs.
"""
 
        response = openai_client.responses.create(
            model=OPENAI_MODEL,
            input=[
                {"role": "system", "content": system_context},
                {"role": "user", "content": prompt},
            ],
            reasoning={"effort": "low"},  # none, low, medium, high
            max_output_tokens=32768,
        )

        html_body = markdown.markdown(response.output_text.strip(), extensions=['nl2br'])
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
