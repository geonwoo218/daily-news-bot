import requests
from bs4 import BeautifulSoup
import datetime
import os

# ==========================================
# 환경변수 설정
# ==========================================
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN') 
CHAT_ID = os.environ.get('CHAT_ID')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
}

def get_news_list():
    url = "https://news.naver.com/section/101"
    res = requests.get(url, headers=HEADERS)
    result_text = ""

    if res.status_code == 200:
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 구조가 미세하게 다를 수 있어 여러 후보군을 탐색
        main_section = soup.find("div", class_="_SECTION_HEADLINE_LIST")
        if not main_section:
            main_section = soup.find("ul", class_="sa_list_news")
        
        if main_section:
            tags = main_section.find_all('strong', class_='sa_text_strong')
            for i, tag in enumerate(tags[:5]):
                result_text += f"{i+1}. {tag.get_text().strip()}\n"
        else:
            # 디버깅을 위해 페이지 타이틀이라도 출력해봄
            result_text = f"뉴스 섹션 찾기 실패 (페이지 제목: {soup.title.get_text() if soup.title else '없음'})"
    else:
        result_text = "접속 실패"
    return result_text

def get_kospi():
    url = "https://finance.naver.com/sise/sise_index.naver?code=KOSPI"
    res = requests.get(url, headers=HEADERS) # 여기도 헤더 추가
    if res.status_code == 200:
        soup = BeautifulSoup(res.text, 'html.parser')
        kospi_val = soup.find('em', id="now_value")
        return f"📉 현재 KOSPI: {kospi_val.get_text()} 포인트" if kospi_val else "정보 없음"
    return "접속 실패"

def get_exchange_rate():
    url = "https://finance.naver.com/marketindex/"
    res = requests.get(url, headers=HEADERS) # 여기도 헤더 추가
    if res.status_code == 200:
        soup = BeautifulSoup(res.text, 'html.parser')
        data_list = soup.find("ul", id="exchangeList")
        if data_list:
            exchange_val = data_list.find("span", class_="value")
            return f"💵 현재 환율(USD): {exchange_val.get_text()}원"
    return "정보 없음"

def send_telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("토큰 에러")
        return

    send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {'chat_id': CHAT_ID, 'text': message}
    requests.get(send_url, params=params)

if __name__ == "__main__":
    # [핵심 수정 2] 깃허브 서버(UTC) 시간에 9시간을 더해 한국 시간(KST)으로 보정
    now_utc = datetime.datetime.utcnow()
    now_kst = now_utc + datetime.timedelta(hours=9)
    today = now_kst.strftime("%Y년 %m월 %d일 %H시 %M분")
    
    news_report = get_news_list()
    market_status = get_kospi()
    exchange_rate = get_exchange_rate()
    
    final_message = f"""
[📅 {today} 경제 브리핑]
{exchange_rate}
{market_status}

[🔥 주요 경제 뉴스]
{news_report}

오늘도 화이팅!
"""
    send_telegram(final_message)
