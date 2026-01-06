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
MY_PORTFOLIO = os.environ.get('MY_PORTFOLIO')
MY_PORTFOLIO = [
    # --- 한국 주식 (KR) ---
    {"name": "카카오", "type": "KR", "code": "035720", "buy_price": 61360, "qty": 1},
    {"name": "KODEX 미국나스닥100", "type": "KR", "code": "379810", "buy_price": 24522, "qty": 2}
]

def get_exchange_rate():
    url = "https://finance.naver.com/marketindex/"
    try:
        res = requests.get(url, headers=HEADERS)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            data_list = soup.find("ul", id="exchangeList")
            if data_list:
                exchange_str = data_list.find("span", class_="value").get_text()
                return float(exchange_str.replace(",", ""))
    except:
        pass
    return 1450.0

def get_kr_stock(code):
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

def get_us_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")
        if not hist.empty:
            return float(hist['Close'].iloc[-1]), hist
    except:
        pass
    return None, None

def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def get_investment_opinion(profit_rate, rsi=None):
    """상황에 따른 조언 생성 (정렬 점수 부여를 위해 키워드 중요)"""
    opinion = ""
    # 우선순위 점수 (낮을수록 상단 배치)
    # 1: 긴급(과매수/과매도/손절)
    # 2: 주의(물타기/수익실현)
    # 3: 관망(Hold)
    priority = 3 

    if rsi is not None:
        if rsi < 30:
            if profit_rate < -10:
                opinion = "🥶과매도 (물타기 기회?)"
                priority = 1
            else:
                opinion = "🥶과매도 (바닥 다지기)"
                priority = 1
        elif rsi > 70:
            if profit_rate > 0:
                opinion = "🔥과매수 (익절 고려)"
                priority = 1
            else:
                opinion = "📈단기급등 (비중축소/손절고려)"
                priority = 1
        else:
            if profit_rate < -10:
                opinion = "존버 (반등 기다림..)"
                priority = 3
            elif profit_rate > 10:
                opinion = "순항 중 🚢"
                priority = 3
            else:
                opinion = "⚖️관망 (Hold)"
                priority = 3
    else:
        if profit_rate < -15:
            opinion = "🚨손절/추매 신중검토"
            priority = 1
        elif profit_rate > 15:
            opinion = "🍬수익실현 고민"
            priority = 2
        else:
            opinion = "🧘Hold"
            priority = 3
            
    return opinion, priority

def analyze_portfolio():
    # 데이터를 먼저 수집해서 리스트에 담음 (정렬을 위해)
    portfolio_data = [] 
    
    total_buy_krw = 0 
    total_now_krw = 0 
    usd_rate = get_exchange_rate()
    
    print(f"환율: {usd_rate}")

    for stock in MY_PORTFOLIO:
        current_price = 0
        rsi_val = None
        
        # 1. 데이터 수집
        if stock['type'] == "KR":
            price = get_kr_stock(stock['code'])
            if not price: continue
            current_price = price
        elif stock['type'] == "US":
            price, hist = get_us_stock_data(stock['code'])
            if not price: continue
            current_price = price
            if hist is not None and len(hist) > 14:
                rsi_val = calculate_rsi(hist)

        # 2. 가치 계산
        current_val_krw = 0
        buy_val_krw = 0
        if stock['type'] == "KR":
            current_val_krw = current_price * stock['qty']
            buy_val_krw = stock['buy_price'] * stock['qty']
        else:
            current_val_krw = (current_price * usd_rate) * stock['qty']
            buy_val_krw = (stock['buy_price'] * usd_rate) * stock['qty']
            
        total_buy_krw += buy_val_krw
        total_now_krw += current_val_krw
        
        profit_rate = ((current_price - stock['buy_price']) / stock['buy_price']) * 100
        
        # 3. 조언 및 우선순위 획득
        advice, priority = get_investment_opinion(profit_rate, rsi_val)
        
        # 정렬을 위해 딕셔너리로 저장
        stock_info = {
            'name': stock['name'],
            'profit_rate': profit_rate,
            'rsi': rsi_val,
            'advice': advice,
            'priority': priority
        }
        portfolio_data.append(stock_info)

    # ==========================================
    # [핵심] 정렬 로직 (Sorting Algorithm)
    # 1순위: Priority (긴급한 것 위로)
    # 2순위: Profit Rate (수익률 낮은 순서대로 - 아픈 손가락 먼저)
    # ==========================================
    portfolio_data.sort(key=lambda x: (x['priority'], x['profit_rate']))

    # 리포트 문자열 생성
    report_lines = []
    report_lines.append(f"💵 환율: ${usd_rate:,.1f}원\n")

    for item in portfolio_data:
        rsi_str = f"(RSI:{item['rsi']:.0f})" if item['rsi'] else ""
        icon = "🔴" if item['profit_rate'] > 0 else "🔵"
        
        # 이름 길이 조절
        name = item['name']
        if len(name) > 8: name = name[:8] + ".."
        
        line = f"{icon} {name}: {item['profit_rate']:+.1f}% {rsi_str}\n"
        line += f"   └ {item['advice']}"
        report_lines.append(line)

    # 전체 요약
    total_profit_rate = 0
    if total_buy_krw > 0:
        total_profit_rate = ((total_now_krw - total_buy_krw) / total_buy_krw) * 100
    total_diff = total_now_krw - total_buy_krw
    
    summary = f"""
📊 [AI 투자 어드바이저]
총 자산: {int(total_now_krw):,}원
평가 손익: {int(total_diff):+,}원 ({total_profit_rate:+.2f}%)
    """
    return summary + "\n" + "\n".join(report_lines)

def get_news_list():
    url = "https://news.naver.com/section/101"
    try:
        res = requests.get(url, headers=HEADERS)
        result_text = ""
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            main_section = soup.find("div", class_="_SECTION_HEADLINE_LIST")
            if not main_section: main_section = soup.find("ul", class_="sa_list_news")
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
    except:
        pass

if __name__ == "__main__":
    now_utc = datetime.datetime.utcnow()
    now_kst = now_utc + datetime.timedelta(hours=9)
    today = now_kst.strftime("%Y년 %m월 %d일")
    
    print("분석 및 정렬 중...")
    portfolio_report = analyze_portfolio()
    news_report = get_news_list()
    
    final_message = f"""
🤖 [{today} JARVIS 투자 브리핑]

{portfolio_report}

📰 [주요 경제 뉴스]
{news_report}

* RSI 기반 우선순위 정렬 완료
    """
    send_telegram(final_message)