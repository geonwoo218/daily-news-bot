import json
import os

DB_FILE = "portfolio.json"

INITIAL_DATA = [
    {"name": "리게티 컴퓨팅", "type": "US", "code": "RGTI", "buy_price": 40.74, "qty": 7.0},
    {"name": "아이렌(IREN)", "type": "US", "code": "IREN", "buy_price": 55.59, "qty": 2.49},
    {"name": "QQQ", "type": "US", "code": "QQQ", "buy_price": 607.82, "qty": 0.172},
    {"name": "아이온큐", "type": "US", "code": "IONQ", "buy_price": 59.67, "qty": 2.03},
    {"name": "엔비디아", "type": "US", "code": "NVDA", "buy_price": 186.20, "qty": 0.547},
    {"name": "SPY", "type": "US", "code": "SPY", "buy_price": 667.76, "qty": 0.14},
    {"name": "마이크로소프트", "type": "US", "code": "MSFT", "buy_price": 494.76, "qty": 0.194},
    {"name": "메타", "type": "US", "code": "META", "buy_price": 649.34, "qty": 0.142},
    {"name": "VOO", "type": "US", "code": "VOO", "buy_price": 618.10, "qty": 0.113},
    {"name": "VTI", "type": "US", "code": "VTI", "buy_price": 330.75, "qty": 0.192},
    {"name": "TSLL", "type": "US", "code": "TSLL", "buy_price": 19.21, "qty": 3.22},
    {"name": "테슬라", "type": "US", "code": "TSLA", "buy_price": 450.04, "qty": 0.1259},
    {"name": "카카오", "type": "KR", "code": "035720", "buy_price": 61360, "qty": 1.0},
    {"name": "KODEX 미국나스닥100", "type": "KR", "code": "379810", "buy_price": 24522, "qty": 2.0},
    {"name": "알파벳 Class A", "type": "US", "code": "GOOGL", "buy_price": 311.67, "qty": 0.095},
    {"name": "오라클", "type": "US", "code": "ORCL", "buy_price": 180.37, "qty": 0.03},
    {"name": "호멜 푸즈", "type": "US", "code": "HRL", "buy_price": 22.84, "qty": 0.08},
    {"name": "애플", "type": "US", "code": "AAPL", "buy_price": 279.82, "qty": 0.0051}
]

def init_database():
    print(f"📂 {DB_FILE} 파일을 생성합니다...")
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(INITIAL_DATA, f, ensure_ascii=False, indent=4)
    print("✅ 데이터베이스 초기화 완료!")
    print(f"총 {len(INITIAL_DATA)}개 종목이 등록되었습니다.")

if __name__ == "__main__":
    init_database()
