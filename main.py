import requests
from bs4 import BeautifulSoup
import datetime
import os # 운영체제(OS)의 환경변수를 가져오는 도구

# ==========================================
# [보안 수정] 코드에 토큰을 직접 적지 않고, 환경변수에서 가져옵니다.
# 내 컴퓨터에서 테스트할 때만 토큰을 직접 적고, 올릴 땐 지우거나 주석 처리하세요.
# ==========================================
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN') 
CHAT_ID = os.environ.get('CHAT_ID')

# (아래 함수들은 기존과 동일합니다. 그대로 두세요.)
def get_news_list():
    # ... (기존 코드 유지) ...
    url = "https://news.naver.com/section/101"
    res = requests.get(url)
    result_text = ""
    if res.status_code == 200:
        soup = BeautifulSoup(res.text, 'html.parser')
        main_section = soup.find("div", class_="_SECTION_HEADLINE_LIST")
        if not main_section:
            main_section = soup.find("ul", class_="sa_list_news") # class 이름 수정됨
        
        if main_section:
            tags = main_section.find_all('strong', class_='sa_text_strong')
            for i, tag in enumerate(tags[:5]):
                result_text += f"{i+1}. {tag.get_text().strip()}\n"
        else:
            result_text = "뉴스 섹션을 찾을 수 없습니다."
    else:
        result_text = "접속 실패"
    return result_text

def get_kospi():
    # ... (기존 코드 유지) ...
    url = "https://finance.naver.com/sise/sise_index.naver?code=KOSPI"
    res = requests.get(url)
    if res.status_code == 200:
        soup = BeautifulSoup(res.text, 'html.parser')
        kospi_val = soup.find('em', id="now_value")
        return f"📉 현재 KOSPI: {kospi_val.get_text()} 포인트" if kospi_val else "정보 없음"
    return "접속 실패"

def get_exchange_rate():
    # ... (기존 코드 유지) ...
    url = "https://finance.naver.com/marketindex/"
    res = requests.get(url)
    if res.status_code == 200:
        soup = BeautifulSoup(res.text, 'html.parser')
        data_list = soup.find("ul", id="exchangeList")
        if data_list:
            exchange_val = data_list.find("span", class_="value")
            return f"💵 현재 환율(USD): {exchange_val.get_text()}원"
    return "정보 없음"

def send_telegram(message):
    # 토큰이 없을 경우(테스트 중 실수 등) 에러 방지
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("토큰이나 ID가 설정되지 않았습니다.")
        return

    send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {'chat_id': CHAT_ID, 'text': message}
    res = requests.get(send_url, params=params)
    if res.status_code == 200:
        print(">> 전송 완료")
    else:
        print(f">> 전송 실패: {res.status_code}")

if __name__ == "__main__":
    today = datetime.datetime.now().strftime("%Y년 %m월 %d일 %H시 %M분")
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