import requests
from bs4 import BeautifulSoup
import datetime
import os
import yfinance as yf # 야후 파이낸스 라이브러리 추가

# ==========================================
# [설정] 텔레그램 토큰 & Chat ID
# ==========================================
# 깃허브 Secrets를 쓰신다면 os.environ.get()을 유지하세요.
# 테스트용이라면 직접 입력해도 되지만, 꼭 비밀로 관리하세요!

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN') 
CHAT_ID = os.environ.get('CHAT_ID')

HEADERS = {
    'User-Agent': 'Mozilla/5.0'
}

# 💰 [내 포트폴리오] 
# 보내주신 이미지의 모든 종목과 평단가, 수량을 완벽하게 반영했습니다.
MY_PORTFOLIO = [

    # --- 한국 주식 (KR) ---
    {"name": "카카오", "type": "KR", "code": "035720", "buy_price": 61360, "qty": 1},
    {"name": "KODEX 미국나스닥100", "type": "KR", "code": "379810", "buy_price": 24522, "qty": 2}
]

def get_exchange_rate():
    """네이버 금융에서 현재 원/달러 환율 가져오기"""
    url = "https://finance.naver.com/marketindex/"
    try:
        res = requests.get(url, headers=HEADERS)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            data_list = soup.find("ul", id="exchangeList")
            if data_list:
                exchange_str = data_list.find("span", class_="value").get_text()
                return float(exchange_str.replace(",", ""))
    except Exception as e:
        print(f"환율 에러: {e}")
    return 1450.0 # 에러 시 기본값

def get_kr_stock(code):
    """네이버 금융에서 한국 주식 현재가 가져오기"""
    url = f"https://finance.naver.com/item/main.naver?code={code}"
    try:
        res = requests.get(url, headers=HEADERS)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            no_today = soup.find("p", class_="no_today")
            if no_today:
                price_text = no_today.find("span", class_="blind").get_text()
                return int(price_text.replace(",", ""))
    except:
        pass
    return None

def get_us_stock(ticker):
    """
    [핵심 변경] yfinance 라이브러리 사용
    네이버처럼 주소가 바뀌거나 막힐 걱정이 전혀 없습니다.
    """
    try:
        # 야후 파이낸스에서 데이터 로딩
        stock = yf.Ticker(ticker)
        
        # 최근 1일치 장마감 데이터(History) 가져오기
        # 미국 시장이 열려있으면 실시간 가격, 닫혀있으면 종가를 가져옵니다.
        hist = stock.history(period="1d")
        
        if not hist.empty:
            # 가장 최근 가격('Close' 컬럼의 마지막 값)
            return float(hist['Close'].iloc[-1])
            
    except Exception as e:
        print(f"{ticker} 로딩 실패: {e}")
        pass
    return None

def analyze_portfolio():
    report = []
    total_buy_krw = 0 
    total_now_krw = 0 
    
    # 1. 환율 가져오기
    usd_rate = get_exchange_rate()
    report.append(f"💵 환율: ${usd_rate:,.1f}원\n")
    
    # 2. 포트폴리오 분석
    for stock in MY_PORTFOLIO:
        current_price = 0
        profit_rate = 0
        line = ""
        
        # 한국 주식
        if stock['type'] == "KR":
            price = get_kr_stock(stock['code'])
            if not price:
                report.append(f"❌ {stock['name']}: 로딩 실패")
                continue
            
            current_price = price
            # 평가금액 계산
            current_val = current_price * stock['qty']
            buy_val = stock['buy_price'] * stock['qty']
            
            profit_rate = ((current_price - stock['buy_price']) / stock['buy_price']) * 100
            
            # 출력 포맷
            line = f"🇰🇷 {stock['name']}: {current_price:,}원 ({profit_rate:+.1f}%)"
            
            total_buy_krw += buy_val
            total_now_krw += current_val

        # 미국 주식
        elif stock['type'] == "US":
            price = get_us_stock(stock['code'])
            if not price:
                report.append(f"❌ {stock['name']}: 로딩 실패")
                continue
                
            current_price = price
            
            # 달러 -> 원화 환산하여 합산
            current_val_krw = (current_price * usd_rate) * stock['qty']
            buy_val_krw = (stock['buy_price'] * usd_rate) * stock['qty']
            
            profit_rate = ((current_price - stock['buy_price']) / stock['buy_price']) * 100
            
            line = f"🇺🇸 {stock['name']}: ${current_price:,.2f} ({profit_rate:+.1f}%)"
            
            total_buy_krw += buy_val_krw
            total_now_krw += current_val_krw
        
        # 이모지 추가 (수익:🔴, 손실:🔵)
        icon = "🔴" if profit_rate > 0 else "🔵"
        report.append(f"{icon} {line}")

    # 3. 전체 계좌 요약
    total_profit_rate = 0
    if total_buy_krw > 0:
        total_profit_rate = ((total_now_krw - total_buy_krw) / total_buy_krw) * 100
    total_diff = total_now_krw - total_buy_krw
    
    summary = f"""
📊 [자산 현황 보고]
총 자산: {int(total_now_krw):,}원
총 손익: {int(total_diff):+,}원 ({total_profit_rate:+.2f}%)
    """
    return summary + "\n" + "\n".join(report)

def get_news_list():
    """뉴스 크롤링 (기존 유지)"""
    url = "https://news.naver.com/section/101"
    try:
        res = requests.get(url, headers=HEADERS)
        result_text = ""
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            main_section = soup.find("div", class_="_SECTION_HEADLINE_LIST")
            if not main_section: main_section = soup.find("ul", class_="sa_list")
            if main_section:
                tags = main_section.find_all('strong', class_='sa_text_strong')
                for i, tag in enumerate(tags[:5]):
                    result_text += f"{i+1}. {tag.get_text().strip()}\n"
        return result_text
    except:
        return "뉴스 정보 없음"

def send_telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {'chat_id': CHAT_ID, 'text': message}
    try:
        requests.get(send_url, params=params)
        print("전송 완료!")
    except:
        print("전송 실패")

if __name__ == "__main__":
    now_utc = datetime.datetime.utcnow()
    now_kst = now_utc + datetime.timedelta(hours=9)
    today = now_kst.strftime("%Y년 %m월 %d일")
    
    print("분석 시작...")
    portfolio_report = analyze_portfolio()
    news_report = get_news_list()
    
    final_message = f"""
💰 [{today} 투자 비서 리포트]

{portfolio_report}

📰 [주요 경제 뉴스]
{news_report}
    """
    send_telegram(final_message)