import datetime
import pytz
import os
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


presets = {
    "AI": ("AI", "fas fa-robot"),
    "Semiconductor": ("반도체", "fas fa-microchip"),
    "Display": ("디스플레이", "fas fa-tv"),
    "Secondary Battery": ("이차전지", "fas fa-battery-half"),
    "Autonomous Driving": ("자율주행", "fas fa-car"),
    "EV": ("전기차", "fas fa-charging-station"),
    "UAM": ("UAM", "fas fa-helicopter"),
    "Aerospace Technology": ("우주 기술", "fas fa-rocket"),
    "Nuclear Energy": ("원자력", "fas fa-atom"),
    "Biotechnology": ("바이오", "fas fa-dna"),
    "Pharmaceuticals": ("의약품", "fas fa-pills"),
    "Digital Health": ("디지털 헬스", "fas fa-heartbeat"),
    "Hydrogen": ("수소", "fas fa-wind"),
    "Cybersecurity": ("사이버보안", "fas fa-shield-alt"),
    "6G": ("6G", "fas fa-wifi"),
    "Robotics": ("로봇", "fas fa-robot"),
    "Quantum": ("양자", "fas fa-cube"),
}

template = env.get_template('contents.html')


for name_eng, (name_kor, icon) in presets.items():

    tech = {'name': name_kor, 'icon': icon}
    with open(f'./output_html/{name_eng}.html', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

        h2_all = soup.find_all('h2')

        topics = []

    for h2 in h2_all:
        topic_name = h2.get_text(strip=True).replace('Topic ', '').split(':', 1)[-1].strip()
        summary_p = h2.find_next('p')
        summary = summary_p.get_text(strip=True).replace('Summary:', '') if summary_p else ""

        # 기사 <a> 태그들은 Summary 다음 <p>에 있음
        article_p = summary_p.find_next_sibling('p') if summary_p else None
        articles = []
        if article_p:
            for a in article_p.find_all('a'):
                title = a.get_text(strip=True)
                url = a.get('href')
                articles.append({"title": title, "url": url})

        topics.append({
            "name": topic_name,
            "summary": summary,
            "articles": articles
        })

    with open(f'./output_html_mobile/{name_eng}.html', 'w', encoding='utf-8') as f:
        f.write(template.render(topics=topics, tech=tech))