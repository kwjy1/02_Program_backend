import datetime
import os

import pandas as pd
import pytz
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader


def collect_topic_nodes(h2):
    nodes = []
    next_tag = h2.find_next_sibling()
    while next_tag is not None and next_tag.name != "h2":
        if getattr(next_tag, "name", None):
            nodes.append(next_tag)
        next_tag = next_tag.find_next_sibling()
    return nodes


def extract_summary(nodes):
    for node in nodes:
        summary_strong = node.find("strong", string=lambda s: s and "Summary" in s)
        if not summary_strong:
            continue

        summary_parts = []
        for sib in summary_strong.next_siblings:
            if getattr(sib, "name", None) == "br":
                continue
            text = sib.get_text(" ", strip=True) if hasattr(sib, "get_text") else str(sib).strip()
            if text:
                summary_parts.append(text)

        return " ".join(summary_parts).lstrip(":").strip()
    return ""


def extract_articles(nodes):
    articles = []
    seen_urls = set()
    in_articles = False

    for node in nodes:
        if node.find("strong", string=lambda s: s and "Articles" in s):
            in_articles = True

        if not in_articles:
            continue

        for a in node.find_all("a"):
            title = a.get_text(strip=True)
            url = a.get("href")
            if title and url and url not in seen_urls:
                articles.append({"title": title, "url": url})
                seen_urls.add(url)

    return articles


output_dir = "output_html_mobile"
os.makedirs(output_dir, exist_ok=True)

file_loader = FileSystemLoader("./templates")
env = Environment(loader=file_loader)

template = env.get_template("index.html")

data = {
    "today": datetime.datetime.now(pytz.timezone("Asia/Seoul")).strftime("%Y.%m.%d.")
}

with open("./output_html_mobile/index.html", "w", encoding="utf-8") as f:
    f.write(template.render(data))

techs = pd.read_csv("tech_preset.csv", index_col=0)
template = env.get_template("contents.html")

for fname, tname, icon in zip(techs["query_eng"], techs["query_kor"], techs["icon"]):
    tech = {"name": tname, "icon": icon}

    with open(f"./output_html/{fname}.html", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")

    topics = []
    for h2 in soup.find_all("h2"):
        topic_nodes = collect_topic_nodes(h2)
        topic_name = h2.get_text(strip=True).replace("Topic ", "").split(":", 1)[-1].strip()

        topics.append({
            "name": topic_name,
            "summary": extract_summary(topic_nodes),
            "articles": extract_articles(topic_nodes),
        })

    with open(f"./output_html_mobile/{fname}.html", "w", encoding="utf-8") as f:
        f.write(template.render(topics=topics, tech=tech))
