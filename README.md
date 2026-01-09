# daily-news-bot

![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python)
![GitHub Actions](https://img.shields.io/badge/Action-Automation-green?logo=githubactions)
![Telegram](https://img.shields.io/badge/Bot-Telegram-blue?logo=telegram)

## 📝 프로젝트 소개 (Overview)
컴퓨터공학 전공 지식을 활용하여 개발한 **개인 맞춤형 주식 포트폴리오 매니저**입니다.
단순히 주가를 조회하는 것을 넘어, **RSI(상대강도지수) 알고리즘**을 통해 과매수/과매도 구간을 판단하고, 투자 우선순위(긴급/주의/관망)에 따라 정렬된 리포트를 **텔레그램**으로 매일 아침 자동 발송합니다.


## 🚀 실행 방법 (How to Run)

### 1. 환경 설정 (Prerequisites)
이 프로젝트는 텔레그램 봇 토큰이 필요합니다.(텔레그램이 무료)

1.  `requirements.txt` 패키지 설치
    ```bash
    pip install -r requirements.txt
    ```
2.  환경 변수 설정 (또는 코드 내 입력)
    * `TELEGRAM_TOKEN`: 봇 파더에게 받은 토큰
    * `CHAT_ID`: 본인의 챗 ID
    * `GEMINI_AP_KEY`:본인의 제미나이 API키
### 2. 실행 (Run)
```bash
python main.py
init_db.py : 초기 데이터 생성하는 코드 한번만 실행하면 됨
portfoli.json : 내 데이터 저장 되어있음
텔레그렘 대화창에
보고 : 포트폴리오 가지고 보고함
뉴스 : 현재 뉴스들 가지고  AI가 요약 보고함
종목 수량 금액 매수 : 종목을 매수함
종목 수량 금액 매도 : 종목을 매도함
