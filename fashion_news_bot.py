import requests
import json
from datetime import datetime, timedelta
import os
import time
from bs4 import BeautifulSoup
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FashionNewsBot:
    def __init__(self):
        # 환경변수에서 API 키들 가져오기
        self.naver_client_id = os.getenv('NAVER_CLIENT_ID')
        self.naver_client_secret = os.getenv('NAVER_CLIENT_SECRET')
        self.slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        
        # 디버깅용 출력
        print(f"🔑 NAVER_CLIENT_ID: {'✅ 설정됨' if self.naver_client_id else '❌ 없음'}")
        print(f"🔑 NAVER_CLIENT_SECRET: {'✅ 설정됨' if self.naver_client_secret else '❌ 없음'}")
        print(f"🔑 SLACK_WEBHOOK_URL: {'✅ 설정됨' if self.slack_webhook_url else '❌ 없음'}")
        
        # 패션 관련 키워드들 (우선순위별 정렬)
        self.fashion_keywords = [
            'K-패션', '패션트렌드', '패션브랜드', '패션산업', '패션기업',
            '의류산업', '패션시장', '패션디자인', '섬유산업', '패션테크', 
            '패션플랫폼', '패션스타트업', '한국패션', '패션위크', 
            '명동패션', '동대문패션', '패션유통', '온라인패션', 
            '패션소비', '지속가능패션', 'SPA브랜드', '패스트패션'
        ]
        
        # 신뢰할 만한 뉴스 소스들
        self.trusted_sources = [
            '연합뉴스', '뉴시스', '뉴스1', '헤럴드경제', 
            '한국경제', '매일경제', '파이낸셜뉴스', '아시아경제',
            '패션비즈', '패션인사이트', '한국섬유신문', '어패럴뉴스',
            'WWD코리아', '섬유저널', '패션채널'
        ]
        
        # 제외할 키워드 (광고성, 홍보성 내용)
        self.exclude_keywords = [
            '할인', '세일', '쿠폰', '이벤트', '프로모션', 
            '광고', '협찬', 'PR', '홍보'
        ]

    def is_valid_news(self, title, description=""):
        """뉴스가 유효한지 확인 (광고성 내용 제외)"""
        content = f"{title} {description}".lower()
        
        # 제외할 키워드가 포함되어 있으면 제외
        if any(exclude_word in content for exclude_word in self.exclude_keywords):
            return False
            
        # 너무 짧은 제목 제외
        if len(title) < 10:
            return False
            
        return True

    def search_naver_news(self, keyword, display=5):
        """네이버 뉴스 API로 뉴스 검색 (개선된 버전)"""
        url = "https://openapi.naver.com/v1/search/news.json"
        headers = {
            'X-Naver-Client-Id': self.naver_client_id,
            'X-Naver-Client-Secret': self.naver_client_secret
        }
        
        # 최근 3일 내 뉴스만 검색하도록 개선
        three_days_ago = (datetime.now() - timedelta(days=3)).strftime('%Y%m%d')
        
        params = {
            'query': f'{keyword} after:{three_days_ago}',
            'display': display,
            'start': 1,
            'sort': 'date'  # 최신순 정렬
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                logger.warning(f"API 호출 제한 도달, 잠시 대기합니다...")
                time.sleep(1)
                return None
            else:
                logger.warning(f"네이버 뉴스 검색 오류({keyword}): {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            logger.warning(f"뉴스 검색 타임아웃({keyword})")
            return None
        except Exception as e:
            logger.warning(f"뉴스 검색 오류({keyword}): {e}")
            return None

    def scrape_fashion_sites(self):
        """패션 전문 사이트에서 뉴스 스크래핑 (개선된 버전)"""
        news_list = []
        
        # 1. 패션비즈 뉴스
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get('https://fashionbiz.co.kr/news/', headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 뉴스 아이템 찾기 (실제 사이트 구조에 맞게 수정 필요)
                articles = soup.select('li.list-item')[:3]  # 최신 3개
                
                for article in articles:
                    title_elem = article.select_one('h3 a') or article.select_one('.title a')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        link = title_elem.get('href', '')
                        if link and not link.startswith('http'):
                            link = 'https://fashionbiz.co.kr' + link
                        
                        if self.is_valid_news(title):
                            news_list.append({
                                'title': title,
                                'link': link,
                                'source': '패션비즈',
                                'pubDate': datetime.now().strftime('%Y-%m-%d'),
                                'description': '패션비즈 최신 뉴스',
                                'keyword': '패션비즈'
                            })
        except Exception as e:
            logger.warning(f"패션비즈 스크래핑 오류: {e}")
        
        # 2. 기타 패션 사이트들도 추가 가능
        # try:
        #     # 패션인사이트, WWD코리아 등 추가 스크래핑
        # except Exception as e:
        #     logger.warning(f"추가 사이트 스크래핑 오류: {e}")
        
        return news_list

    def collect_daily_news(self):
        """일일 패션 뉴스 수집 (개선된 로직)"""
        all_news = []
        
        # API 키 확인
        if not self.naver_client_id or not self.naver_client_secret:
            print("❌ 네이버 API 키가 설정되지 않았습니다. 테스트 뉴스를 사용합니다.")
            return [{
                'title': '[테스트] 패션 뉴스봇 정상 작동 확인',
                'description': '네이버 API 키를 설정하면 실제 패션 뉴스를 수집합니다.',
                'link': 'https://github.com',
                'source': '패션뉴스봇',
                'pubDate': datetime.now().strftime('%Y-%m-%d'),
                'keyword': '테스트'
            }]
        
        print("🔍 네이버 API로 뉴스 검색 중...")
        
        # 1. 네이버 API로 키워드별 검색 (주요 키워드 위주)
        success_count = 0
        for keyword in self.fashion_keywords[:8]:  # API 제한 고려하여 8개만
            news_data = self.search_naver_news(keyword, display=4)
            
            if news_data and 'items' in news_data:
                success_count += 1
                for item in news_data['items']:
                    try:
                        # HTML 태그 제거 및 정제
                        title = BeautifulSoup(item['title'], 'html.parser').get_text().strip()
                        description = BeautifulSoup(item['description'], 'html.parser').get_text().strip()
                        
                        # 유효성 검사
                        if not self.is_valid_news(title, description):
                            continue
                        
                        # 발행일 파싱
                        pub_date = item.get('pubDate', '')
                        if pub_date:
                            try:
                                # RFC 2822 형식을 datetime으로 변환
                                import email.utils
                                pub_datetime = email.utils.parsedate_to_datetime(pub_date)
                                formatted_date = pub_datetime.strftime('%Y-%m-%d')
                            except:
                                formatted_date = datetime.now().strftime('%Y-%m-%d')
                        else:
                            formatted_date = datetime.now().strftime('%Y-%m-%d')
                        
                        all_news.append({
                            'title': title,
                            'description': description[:200],  # 설명 길이 제한
                            'link': item.get('originallink', item.get('link', '')),
                            'source': '네이버뉴스',
                            'pubDate': formatted_date,
                            'keyword': keyword
                        })
                        
                    except Exception as e:
                        logger.warning(f"뉴스 아이템 처리 오류: {e}")
                        continue
            
            # API 호출 간격 조절
            time.sleep(0.2)
        
        print(f"✅ {success_count}개 키워드로 뉴스 검색 완료")
        
        # 2. 패션 전문 사이트 스크래핑
        print("🔍 패션 전문 사이트 스크래핑 중...")
        scraped_news = self.scrape_fashion_sites()
        all_news.extend(scraped_news)
        
        # 3. 중복 제거 및 품질 필터링
        seen_titles = set()
        unique_news = []
        
        for news in all_news:
            # 제목 기준 중복 제거 (유사도 검사 개선)
            title_key = news['title'].lower().replace(' ', '')
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_news.append(news)
        
        # 4. 뉴스 정렬 (최신순)
        try:
            unique_news.sort(key=lambda x: x['pubDate'], reverse=True)
        except:
            pass  # 정렬 실패 시 기존 순서 유지
        
        # 5. 상위 12개만 선택
        final_news = unique_news[:12]
        
        # 6. 뉴스가 없으면 알림 메시지
        if not final_news:
            final_news = [{
                'title': '📢 오늘은 새로운 패션 뉴스가 없습니다',
                'description': '내일 다시 확인해주세요! 패션 업계의 새로운 소식을 기다려봅니다.',
                'link': 'https://fashionbiz.co.kr',
                'source': '패션뉴스봇',
                'pubDate': datetime.now().strftime('%Y-%m-%d'),
                'keyword': '알림'
            }]
        
        return final_news

    def format_slack_message(self, news_list):
        """슬랙 메시지 포맷 생성 (개선된 디자인)"""
        today = datetime.now().strftime('%Y년 %m월 %d일')
        weekday = ['월', '화', '수', '목', '금', '토', '일'][datetime.now().weekday()]
        
        # 뉴스 유형별 이모지
        emoji_map = {
            'K-패션': '🇰🇷',
            '패션트렌드': '✨',
            '패션브랜드': '👗',
            '패션산업': '🏭',
            '패션테크': '💻',
            'default': '📰'
        }
        
        message = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🎨 {today}({weekday}) 패션 뉴스 브리핑",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"오늘의 한국 패션 업계 주요 소식 *{len(news_list)}건*을 전해드립니다! 🚀"
                    }
                },
                {
                    "type": "divider"
                }
            ]
        }
        
        # 뉴스별로 블록 추가
        for i, news in enumerate(news_list, 1):
            # 키워드에 따른 이모지 선택
            keyword_emoji = emoji_map.get(news.get('keyword', ''), emoji_map['default'])
            
            # 설명 길이 조정
            description = news.get('description', '')
            if len(description) > 120:
                description = description[:120] + '...'
            
            news_block = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{keyword_emoji} *{news['title']}*\n"
                           f"_{description}_\n"
                           f"📰 {news.get('source', '알 수 없음')} • "
                           f"#{news.get('keyword', '패션뉴스')}"
                }
            }
            
            # 링크가 있으면 버튼 추가
            if news.get('link') and news['link'] != 'https://github.com':
                news_block["accessory"] = {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "자세히 보기",
                        "emoji": True
                    },
                    "url": news['link'],
                    "action_id": f"news_button_{i}"
                }
            
            message["blocks"].append(news_block)
            
            # 마지막이 아니면 구분선 추가
            if i < len(news_list):
                message["blocks"].append({"type": "divider"})
        
        # 푸터 개선
        message["blocks"].extend([
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🤖 패션뉴스봇 v2.0 | 업데이트: {datetime.now().strftime('%H:%M')} | "
                               "문의: IT팀"
                    }
                ]
            }
        ])
        
        return message

    def send_to_slack(self, news_list):
        """슬랙으로 메시지 전송 (개선된 오류 처리)"""
        if not self.slack_webhook_url:
            print("❌ 슬랙 웹훅 URL이 설정되지 않았습니다.")
            print("💡 SLACK_WEBHOOK_URL 환경변수를 설정해주세요.")
            return False
        
        if not news_list:
            print("📰 전송할 뉴스가 없습니다.")
            return False
        
        message = self.format_slack_message(news_list)
        
        try:
            response = requests.post(
                self.slack_webhook_url,
                data=json.dumps(message),
                headers={
                    'Content-Type': 'application/json; charset=utf-8'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"✅ 슬랙 전송 완료: {len(news_list)}개 뉴스")
                return True
            else:
                print(f"❌ 슬랙 전송 실패: HTTP {response.status_code}")
                print(f"응답 내용: {response.text[:200]}...")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ 슬랙 전송 타임아웃")
            return False
        except Exception as e:
            print(f"❌ 슬랙 전송 오류: {e}")
            return False

    def run_daily_job(self):
        """일일 뉴스 수집 및 전송 작업 (개선된 로깅)"""
        start_time = datetime.now()
        print(f"🔍 {start_time.strftime('%Y-%m-%d %H:%M')} - 패션 뉴스 수집 시작")
        
        try:
            # 뉴스 수집
            news_list = self.collect_daily_news()
            
            if news_list:
                print(f"📰 {len(news_list)}개의 뉴스를 수집했습니다.")
                
                # 수집된 뉴스 미리보기 출력
                for i, news in enumerate(news_list[:3], 1):
                    print(f"   {i}. {news['title'][:50]}...")
                
                if len(news_list) > 3:
                    print(f"   ... 외 {len(news_list) - 3}개")
                
                # 슬랙 전송
                success = self.send_to_slack(news_list)
                
                if success:
                    end_time = datetime.now()
                    duration = (end_time - start_time).seconds
                    print(f"✅ 패션 뉴스 브리핑 완료! (소요시간: {duration}초)")
                else:
                    print("❌ 슬랙 전송에 실패했습니다.")
            else:
                print("📰 수집된 뉴스가 없습니다.")
                
        except Exception as e:
            logger.error(f"작업 실행 중 오류 발생: {e}")
            print(f"❌ 작업 실행 중 오류가 발생했습니다: {e}")

def main():
    """메인 실행 함수"""
    print("=" * 50)
    print("🎨 패션 뉴스봇 v2.0 시작")
    print("=" * 50)
    
    bot = FashionNewsBot()
    
    try:
        bot.run_daily_job()
    except KeyboardInterrupt:
        print("\n⏹️  사용자에 의해 중단되었습니다.")
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        print(f"❌ 예상치 못한 오류가 발생했습니다: {e}")
    finally:
        print("=" * 50)
        print("✅ 패션 뉴스봇 종료")
        print("=" * 50)

if __name__ == "__main__":
    main()
