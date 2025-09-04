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
                    "text": {"type": "plain_text", "text": "기사 보기", "emoji": True},
                    "url": n["link"]
                }
            blocks.append(section)
            if i < len(news_list):
                blocks.append({"type": "divider"})

        blocks.append({
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": f"🤖 패션뉴스봇 | 업데이트 {datetime.now().strftime('%H:%M')}"}
            ]
        })
        return {"blocks": blocks}

        def send_to_slack(self, news_list):
        """슬랙으로 메시지 전송"""
        if not self.slack_webhook_url:
            print("❌ Slack Webhook URL 없음")
            return False

        headers = {"Content-Type": "application/json"}

        # 뉴스가 없으면 하트비트 메시지 전송
        if not news_list:
            payload = {
                "text": f"🫡 오늘은 수집된 패션 뉴스가 없습니다. ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
            }
        else:
            payload = self.format_slack_message(news_list)

        try:
            response = requests.post(
                self.slack_webhook_url,
                data=json.dumps(payload, ensure_ascii=False),
                headers=headers,
                timeout=10
            )
            print("Slack response:", response.status_code, response.text[:200])
            response.raise_for_status()

            if response.text.strip().lower() == "ok" or response.status_code == 200:
                print(f"✅ Slack 전송 완료: {len(news_list)}건")
                return True
            else:
                print("⚠️ Slack 응답 이상:", response.text)
                return False

        except Exception as e:
            print(f"❌ Slack 전송 오류: {e}")
            return False


def main():
    """메인 실행 함수"""
    bot = FashionNewsBot()
    news_list = bot.collect_daily_news()
    bot.send_to_slack(news_list)


if __name__ == "__main__":
    main()
