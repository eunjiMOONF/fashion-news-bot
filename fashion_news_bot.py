# -*- coding: utf-8 -*-
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
        # 환경변수에서 API 키들 가져오기 (없으면 직접 설정된 값 사용)
        self.naver_client_id = os.getenv('NAVER_CLIENT_ID') or "pPilWOLS9m2zOgfbQ24A"
        self.naver_client_secret = os.getenv('NAVER_CLIENT_SECRET') or "mPg8xJxCPy"
        self.slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL') or "https://hooks.slack.com/services/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"
        
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
                logger.warning("API 호출 제한 도달, 잠시 대기합니다...")
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
                        if link a
