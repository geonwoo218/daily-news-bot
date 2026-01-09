import requests
import json
import time
import os
import yfinance as yf
import pandas as pd
from bs4 import BeautifulSoup
import google.generativeai as genai
from dotenv import load_dotenv


# ==========================================
# [설정] 키 입력 (보안 주의!)
# ==========================================
TELEGRAM_TOKEN = "여기에_텔레그램_토큰을_입력하세요"
GEMINI_API_KEY = "여기에_구글_AI_키를_입력하세요"

load_dotenv()
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN') 
CHAT_ID = os.environ.get('CHAT_ID')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

HEADERS = {'User-Agent': 'Mozilla/5.0'}
DB_FILE = "portfolio.json"

# AI 설정 (무료/고속 모델인 flash 사용)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# ==========================================
# 1. 데이터베이스(JSON) 관리
# ==========================================
def load_portfolio():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except: return []

def save_portfolio(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ==========================================
# 2. 거래 처리 로직 (매수/매도)
# ==========================================
def trade_stock(name, qty, price, trade_type):
    portfolio = load_portfolio()
    # 이름이 같거나 코드가 같은 종목 찾기
    target = next((s for s in portfolio if s['name'] == name or s.get('code') == name), None)
    
    msg = ""
    if trade_type == "매수":
        if target:
            # 물타기 (평단가 수정)
            old_amt = target['buy_price'] * target['qty']
            new_amt = price * qty
            target['qty'] += qty
            target['buy_price'] = (old_amt + new_amt) / target['qty']
            msg = f"✅ [추가매수] {target['name']}\n수량: {target['qty']:.2f}주\n평단: {target['buy_price']:.2f}"
        else:
            # 신규 매수 (기본적으로 US로 가정, 숫자로만 된 6자리는 KR로 추정)
            s_type = "KR" if name.isdigit() and len(name)==6 else "US"
            new_stock = {"name": name, "type": s_type, "code": name, "buy_price": price, "qty": qty}
            portfolio.append(new_stock)
            msg = f"✨ [신규매수] {name} 등록 완료!"
            
    elif trade_type == "매도":
        if target:
            if target['qty'] >= qty:
                target['qty'] -= qty
                msg = f"🔵 [매도] {target['name']} {qty}주 처분"
                if target['qty'] == 0:
                    portfolio.remove(target)
                    msg += "\n(전량 매도로 목록 삭제)"
            else:
                msg = "🚫 에러: 보유 수량 부족"
        else:
            msg = "🚫 에러: 보유하지 않은 종목"
            
    save_portfolio(portfolio)
    return msg

# ==========================================
# 3. 데이터 수집 및 AI 분석
# ==========================================
def get_exchange_rate():
    try:
        res = requests.get("https://finance.naver.com/marketindex/", headers=HEADERS)
        val = BeautifulSoup(res.text, 'html.parser').find("span", class_="value").get_text()
        return float(val.replace(",", ""))
    except: return 1450.0

def get_kr_stock(code):
    try:
        url = f"https://finance.naver.com/item/main.naver?code={code}"
        res = requests.get(url, headers=HEADERS)
        no_today = BeautifulSoup(res.text, 'html.parser').find("p", class_="no_today")
        if no_today: return int(no_today.find("span", class_="blind").get_text().replace(",", ""))
    except: pass
    return None

def get_us_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")
        if not hist.empty:
            return float(hist['Close'].iloc[-1]), hist
    except: pass
    return None, None

def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def get_investment_opinion(profit_rate, rsi=None):
    """수익률과 RSI를 종합하여 투자 의견 및 우선순위(Priority) 반환"""
    opinion = ""; priority = 3
    if rsi is not None:
        if rsi < 30:
            opinion = "🥶과매도 (물타기 기회?)" if profit_rate < -10 else "🥶과매도 (바닥 다지기)"
            priority = 1
        elif rsi > 70:
            opinion = "🔥과매수 (익절 고려)" if profit_rate > 0 else "📈단기급등 (비중축소 고려)"
            priority = 1
        else:
            opinion = "⚖️관망 (Hold)"
    else:
        if profit_rate < -15: opinion, priority = "🚨손절/추매 신중검토", 1
        elif profit_rate > 15: opinion, priority = "🍬수익실현 고민", 2
        else: opinion = "🧘Hold"
    return opinion, priority

def get_ai_news_briefing():
    """네이버 뉴스를 긁어와서 AI에게 요약을 시킴"""
    url = "https://news.naver.com/section/101"
    try:
        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.text, 'html.parser')
        news = []
        # 뉴스 섹션 찾기
        sec = soup.find("div", class_="_SECTION_HEADLINE_LIST") or soup.find("ul", class_="sa_list")
        if sec:
            for tag in sec.find_all('strong', class_='sa_text_strong')[:5]:
                news.append(f"- {tag.get_text().strip()}")
        news_text = "\n".join(news)
        
        prompt = f"투자 비서로서 다음 뉴스를 읽고 3줄 요약과 시장 분위기(이모지 포함)를 브리핑해줘:\n{news_text}"
        return model.generate_content(prompt).text
    except Exception as e:
        return f"뉴스 분석 실패: {e}"

# ==========================================
# 4. 포트폴리오 분석 (정렬 포함)
# ==========================================
def analyze_portfolio():
    portfolio = load_portfolio()
    if not portfolio: return "📭 장부가 비어있습니다."
    
    usd_rate = get_exchange_rate()
    portfolio_data = []
    total_val = 0; total_buy = 0
    
    for stock in portfolio:
        current_price = 0; rsi_val = None
        
        # 가격 조회
        if stock['type'] == "US":
            p, h = get_us_stock_data(stock['code'])
            if p: 
                current_price = p
                if h is not None and len(h) > 14: rsi_val = calculate_rsi(h)
        else:
            p = get_kr_stock(stock['code'])
            if p: current_price = p
            
        # 가격 조회를 못했으면 평단가로 대체 (에러 방지)
        if current_price == 0: current_price = stock['buy_price']
            
        # 가치 계산
        rate = usd_rate if stock['type'] == "US" else 1.0
        val = (current_price * rate) * stock['qty']
        buy = (stock['buy_price'] * rate) * stock['qty']
        
        profit_rate = ((current_price - stock['buy_price']) / stock['buy_price']) * 100
        advice, priority = get_investment_opinion(profit_rate, rsi_val)
        
        portfolio_data.append({
            'name': stock['name'], 'profit': profit_rate, 'rsi': rsi_val,
            'advice': advice, 'priority': priority, 'val': val, 'buy': buy
        })
        total_val += val; total_buy += buy

    # [정렬] 1순위: Priority(긴급), 2순위: Profit(수익률 낮은순)
    portfolio_data.sort(key=lambda x: (x['priority'], x['profit']))
    
    # 리포트 작성
    report = [f"💵 환율: {usd_rate:,.1f}원\n"]
    for item in portfolio_data:
        rsi_str = f"(RSI:{item['rsi']:.0f})" if item['rsi'] else ""
        icon = "🔴" if item['profit'] >= 0 else "🔵"
        name = item['name'][:8] + ".." if len(item['name']) > 8 else item['name']
        
        line = f"{icon} {name}: {item['profit']:+.1f}% {rsi_str}\n   └ {item['advice']}"
        report.append(line)
        
    total_profit = ((total_val - total_buy) / total_buy) * 100 if total_buy > 0 else 0
    diff = total_val - total_buy
    
    summary = f"📊 총 자산: {int(total_val):,}원\n손익: {int(diff):+,}원 ({total_profit:+.2f}%)"
    return summary + "\n\n" + "\n".join(report)

# ==========================================
# 5. 텔레그램 봇 메인 루프
# ==========================================
def get_updates(offset=None):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        return requests.get(url, params={'timeout': 20, 'offset': offset}).json()
    except: return {}

def send_msg(chat_id, text):
    try:
        requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", params={'chat_id': chat_id, 'text': text})
    except: pass

def main():
    print("🤖 JARVIS 시스템 가동 중...")
    last_update_id = None
    
    while True:
        try:
            updates = get_updates(last_update_id)
            if "result" in updates and len(updates["result"]) > 0:
                for item in updates["result"]:
                    last_update_id = item["update_id"] + 1
                    chat_id = item["message"]["chat"]["id"]
                    text = item["message"].get("text", "")
                    
                    print(f"📩 수신: {text}")
                    
                    if text == "뉴스":
                        send_msg(chat_id, "🧠 뉴스 분석 중...")
                        send_msg(chat_id, get_ai_news_briefing())
                    elif text == "보고":
                        send_msg(chat_id, "🔍 자산 분석 및 정렬 중...")
                        send_msg(chat_id, analyze_portfolio())
                    elif len(text.split()) == 4: # 예: QQQ 1 500 매수
                        p = text.split()
                        res = trade_stock(p[0], float(p[1]), float(p[2]), p[3])
                        send_msg(chat_id, res)
                    else:
                        send_msg(chat_id, "💡 명령어:\n- [뉴스]\n- [보고]\n- [종목명 수량 가격 매수/매도]")
            time.sleep(1)
        except Exception as e:
            print(f"에러 발생: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()