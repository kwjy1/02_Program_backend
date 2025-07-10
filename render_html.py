import datetime
import pytz
import os
import pandas as pd
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

output_dir = "output_html_mobile"
os.makedirs(output_dir, exist_ok=True)

# Render index.html with current date
file_loader = FileSystemLoader('./templates')
env = Environment(loader=file_loader)

template = env.get_template('index.html')

data = {
    "today": datetime.datetime.now(pytz.timezone('Asia/Seoul')).strftime("%Y.%m.%d.")
}

with open('./output_html_mobile/index.html', 'w', encoding='utf-8') as f:
    f.write(template.render(data))

techs = pd.read_csv("tech_preset.csv", index_col=0)

template = env.get_template('contents.html')


for fname, tname, icon in zip(techs['query_eng'], techs['query_kor'], techs['icon']):

    tech = {'name': tname, 'icon': icon}
    with open(f'./output_html/{fname}.html', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

        h2_all = soup.find_all('h2')

        topics = []

    for h2 in h2_all:
        topic_name = h2.get_text(strip=True).replace('Topic ', '').split(':', 1)[-1].strip()
        summary = ""
        articles = []

        # h2 다음에 나오는 <p> 태그들(최대 2개)만 조사
        p_tags = []
        next_tag = h2
        while len(p_tags) < 2:
            next_tag = next_tag.find_next_sibling()
            if next_tag is None or next_tag.name == 'h2':
                break
            if next_tag.name == 'p':
                p_tags.append(next_tag)

        # 각 <p>에서 summary/articles 추출
        for p in p_tags:
            # Summary 추출
            summary_strong = p.find('strong', string=lambda s: s and 'Summary' in s)
            if summary_strong and not summary:
                summary_text = ""
                for sib in summary_strong.next_siblings:
                    if getattr(sib, 'name', None) == 'br':
                        continue
                    if isinstance(sib, str):
                        summary_text = sib.strip()
                        if summary_text:
                            break
                summary = summary_text.lstrip(':').strip() if summary_text else ""
            # Articles 추출
            articles_strong = p.find('strong', string=lambda s: s and 'Articles' in s)
            if articles_strong:
                for sib in articles_strong.next_siblings:
                    if getattr(sib, 'name', None) == 'a':
                        title = sib.get_text(strip=True)
                        url = sib.get('href')
                        articles.append({"title": title, "url": url})
                # 혹시 <a>가 없으면 <a> 전부 추가
                if not articles:
                    for a in p.find_all('a'):
                        title = a.get_text(strip=True)
                        url = a.get('href')
                        articles.append({"title": title, "url": url})

        topics.append({
            "name": topic_name,
            "summary": summary,
            "articles": articles
        })

    with open(f'./output_html_mobile/{fname}.html', 'w', encoding='utf-8') as f:
        f.write(template.render(topics=topics, tech=tech))