import os, json, time, requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

class FashionNewsBot:
    def __init__(self):
        self.naver_client_id = os.getenv("NAVER_CLIENT_ID")
        self.naver_client_secret = os.getenv("NAVER_CLIENT_SECRET")
        self.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")

        self.fashion_keywords = [
            "패션산업", "패션트렌드", "패션기업", "K-패션",
            "패션브랜드", "의류산업", "패션시장", "패션디자인",
            "동대문패션", "지속가능패션"
        ]

        self.trusted_sources = [
            "연합뉴스", "뉴시스", "뉴스1", "헤럴드경제",
            "한국경제", "매일경제", "파이낸셜뉴스", "아시아경제",
            "패션비즈", "패션인사이트", "한국섬유신문", "어패럴뉴스"
        ]

    def search_naver_news(self, keyword, display=3):
        url = "https://openapi.naver.com/v1/search/news.json"
        headers = {
            "X-Naver-Client-Id": self.naver_client_id,
            "X-Naver-Client-Secret": self.naver_client_secret
        }
        params = {"query": keyword, "display": display, "start": 1, "sort": "date"}

        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[WARN] 네이버 뉴스 검색 오류({keyword}): {e}")
            return None

    def collect_daily_news(self):
        all_news = []
        for kw in self.fashion_keywords[:5]:
            data = self.search_naver_news(kw)
            if not data or "items" not in data:
                continue
            for item in data["items"]:
                title = BeautifulSoup(item["title"], "html.parser").get_text()
                desc = BeautifulSoup(item["description"], "html.parser").get_text()
                link = item.get("originallink") or item.get("link")

                if any(src in title for src in self.trusted_sources):
                    all_news.append({
                        "title": title,
                        "description": desc,
                        "link": link,
                        "source": "네이버뉴스",
                        "keyword": kw,
                        "pubDate": item.get("pubDate", "")
                    })
            time.sleep(0.2)

        return all_news[:15]

    def format_slack_message(self, news_list):
        today = datetime.now().strftime("%Y년 %m월 %d일")
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"🎨 {today} 한국 패션 뉴스 브리핑", "emoji": True}
            },
            {"type": "divider"}
        ]

        for i, n in enumerate(news_list, 1):
            txt = f"*{i}. {n['title']}*\n_{n['description'][:100]}..._"
            section = {"type": "section", "text": {"type": "mrkdwn", "text": txt}}
            if n.get("link"):
                section["accessory"] = {
                    "type": "button",
