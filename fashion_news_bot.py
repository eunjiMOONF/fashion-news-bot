import requests
import json
from datetime import datetime, timedelta
import os
import time
from bs4 import BeautifulSoup

class FashionNewsBot:
    def __init__(self):
        # 환경변수에서 API 키들 가져오기
        self.naver_client_id = os.getenv('NAVER_CLIENT_ID') or os.environ.get('NAVER_CLIENT_ID')
        self.naver_client_secret = os.getenv('NAVER_CLIENT_SECRET') or os.environ.get('NAVER_CLIENT_SECRET')
        self.slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL') or os.environ.get('SLACK_WEBHOOK_URL')
        
        # 디버깅용 출력
        print(f"🔑 NAVER_CLIENT_ID: {'✅ 설정됨' if self.naver_client_id else '❌ 없음'}")
        print(f"🔑 NAVER_CLIENT_SECRET: {'✅ 설정됨' if self.naver_client_secret else '❌ 없음'}")
        print(f"🔑 SLACK_WEBHOOK_URL: {'✅ 설정됨' if self.slack_webhook_url else '❌ 없음'}")
        
        # 패션 관련 키워드들
        self.fashion_keywords = [
            '패션산업', '패션트렌드', '패션기업', 'K-패션', 
            '패션브랜드', '의류산업', '패션시장', '패션디자인',
            '섬유산업', '패션테크', '패션플랫폼', '패션스타트업',
            '한국패션', '패션위크', '명동패션', '동대문패션',
            '패션유통', '온라인패션', '패션소비', '지속가능패션'
        ]
        
        # 신뢰할 만한 뉴스 소스들
        self.trusted_sources = [
            '연합뉴스', '뉴시스', '뉴스1', '헤럴드경제', 
            '한국경제', '매일경제', '파이낸셜뉴스', '아시아경제',
            '패션비즈', '패션인사이트', '한국섬유신문', '어패럴뉴스'
        ]

    def search_naver_news(self, keyword, display=10):
        """네이버 뉴스 API로 뉴스 검색"""
        url = "https://openapi.naver.com/v1/search/news.json"
        headers = {
            'X-Naver-Client-Id': self.naver_client_id,
            'X-Naver-Client-Secret': self.naver_client_secret
        }
        
        params = {
            'query': keyword,
            'display': display,
            'start': 1,
            'sort': 'date'  # 최신순 정렬
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"[WARN] 네이버 뉴스 검색 오류({keyword}): {response.status_code} {response.reason} for url: {response.url}")
                return None
        except Exception as e:
            print(f"[WARN] 뉴스 검색 오류({keyword}): {e}")
            return None

    def scrape_fashion_sites(self):
        """패션 전문 사이트에서 뉴스 스크래핑"""
        news_list = []
        
        # 패션비즈 최신 뉴스
        try:
            response = requests.get('https://fashionbiz.co.kr/news/list.htm', timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                articles = soup.find_all('div', class_='news-item')[:5]  # 최신 5개
                
                for article in articles:
                    title_elem = article.find('h3') or article.find('a')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        link = title_elem.get('href', '')
                        if link and not link.startswith('http'):
                            link = 'https://fashionbiz.co.kr' + link
                        
                        news_list.append({
                            'title': title,
                            'link': link,
                            'source': '패션비즈',
                            'pubDate': datetime.now().strftime('%Y-%m-%d'),
                            'description': '패션비즈 뉴스'
                        })
        except Exception as e:
            print(f"[WARN] 패션비즈 스크래핑 오류: {e}")
        
        return news_list

    def collect_daily_news(self):
        """일일 패션 뉴스 수집"""
        all_news = []
        
        # API 키 확인
        if not self.naver_client_id or not self.naver_client_secret:
            print("❌ 네이버 API 키가 설정되지 않았습니다. 테스트 뉴스를 사용합니다.")
            # 테스트 뉴스 반환
            return [{
                'title': '[테스트] 패션 뉴스봇 정상 작동 확인',
                'description': '네이버 API 키 설정 후 실제 뉴스가 수집됩니다.',
                'link': 'https://github.com',
                'source': '테스트',
                'pubDate': datetime.now().strftime('%Y-%m-%d'),
                'keyword': '테스트'
            }]
        
        # 1. 네이버 API로 키워드별 검색
        for keyword in self.fashion_keywords[:5]:  # API 제한을 고려해 주요 키워드만
            news_data = self.search_naver_news(keyword, display=3)
            if news_data and 'items' in news_data:
                for item in news_data['items']:
                    # HTML 태그 제거
                    title = BeautifulSoup(item['title'], 'html.parser').get_text()
                    description = BeautifulSoup(item['description'], 'html.parser').get_text()
                    
                    # 신뢰할 만한 소스인지 확인
                    if any(source in item.get('originallink', '') or source in title for source in self.trusted_sources):
                        all_news.append({
                            'title': title,
                            'description': description,
                            'link': item.get('originallink', item.get('link', '')),
                            'source': '네이버뉴스',
                            'pubDate': item.get('pubDate', ''),
                            'keyword': keyword
                        })
            
            time.sleep(0.1)  # API 호출 제한 고려
        
        # 2. 패션 전문 사이트 스크래핑
        scraped_news = self.scrape_fashion_sites()
        all_news.extend(scraped_news)
        
        # 중복 제거 (제목 기준)
        seen_titles = set()
        unique_news = []
        for news in all_news:
            if news['title'] not in seen_titles:
                seen_titles.add(news['title'])
                unique_news.append(news)
        
        # 뉴스가 없으면 테스트 뉴스 추가
        if not unique_news:
            unique_news = [{
                'title': '[알림] 오늘은 새로운 패션 뉴스가 없습니다',
                'description': '내일 다시 확인해주세요!',
                'link': 'https://github.com',
                'source': '패션뉴스봇',
                'pubDate': datetime.now().strftime('%Y-%m-%d'),
                'keyword': '알림'
            }]
        
        # 최신순으로 정렬하고 상위 15개만
        return unique_news[:15]

    def format_slack_message(self, news_list):
        """슬랙 메시지 포맷 생성"""
        today = datetime.now().strftime('%Y년 %m월 %d일')
        
        message = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🎨 {today} 한국 패션 뉴스 브리핑",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"오늘의 패션 업계 주요 뉴스 *{len(news_list)}건*을 전해드립니다!"
                    }
                },
                {
                    "type": "divider"
                }
            ]
        }
        
        # 뉴스별로 블록 추가
        for i, news in enumerate(news_list, 1):
            news_block = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{i}. {news['title']}*\n"
                           f"_{news.get('description', '')[:100]}{'...' if len(news.get('description', '')) > 100 else ''}_\n"
                           f"📰 {news.get('source', '알 수 없음')} | "
                           f"{news.get('keyword', '패션뉴스')}"
                }
            }
            
            if news.get('link'):
                news_block["accessory"] = {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "기사 보기",
                        "emoji": True
                    },
                    "url": news['link'],
                    "action_id": f"news_{i}"
                }
            
            message["blocks"].append(news_block)
            
            # 뉴스 간 구분선
            if i < len(news_list):
                message["blocks"].append({"type": "divider"})
        
        # 푸터 추가
        message["blocks"].append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "🤖 패션뉴스봇이 수집한 정보입니다 | "
                           f"마지막 업데이트: {datetime.now().strftime('%H:%M')}"
                }
            ]
        })
        
        return message

    def send_to_slack(self, news_list):
        """슬랙으로 메시지 전송"""
        if not self.slack_webhook_url:
            print("❌ 슬랙 웹훅 URL이 설정되지 않았습니다.")
            return False
        
        if not news_list:
            print("📰 오늘은 새로운 패션 뉴스가 없습니다.")
            return False
        
        message = self.format_slack_message(news_list)
        
        try:
            response = requests.post(
                self.slack_webhook_url,
                data=json.dumps(message),
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                print(f"✅ 슬랙 전송 완료: {len(news_list)}개 뉴스")
                return True
            else:
                print(f"❌ 슬랙 전송 실패: {response.status_code}")
                print(f"응답: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 슬랙 전송 오류: {e}")
            return False

    def run_daily_job(self):
        """일일 뉴스 수집 및 전송 작업"""
        print(f"🔍 {datetime.now().strftime('%Y-%m-%d %H:%M')} - 패션 뉴스 수집 시작")
        
        # 뉴스 수집
        news_list = self.collect_daily_news()
        
        if news_list:
            print(f"📰 {len(news_list)}개의 뉴스를 수집했습니다.")
            
            # 슬랙 전송
            success = self.send_to_slack(news_list)
            
            if success:
                print("✅ 오늘의 패션 뉴스 브리핑이 완료되었습니다!")
            else:
                print("❌ 슬랙 전송에 실패했습니다.")
        else:
            print("📰 수집된 뉴스가 없습니다.")

def main():
    """메인 실행 함수"""
    bot = FashionNewsBot()
    print("🔍 패션 뉴스 수집을 시작합니다...")
    bot.run_daily_job()
    print("✅ 작업이 완료되었습니다!")

if __name__ == "__main__":
    main()
