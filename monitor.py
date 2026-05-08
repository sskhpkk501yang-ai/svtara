import requests
import os

# ── 공연 정보 ──────────────────────────────────────────
GOODS_CODE = "26005973"   # DxS ［소야곡］ ON STAGE - DAEGU
PERF_URL   = f"https://tickets.interpark.com/goods/{GOODS_CODE}"
BASE_URL   = "https://api-ticketfront.interpark.com"

# 모니터링할 날짜 (YYYYMMDD)
PLAY_DATES = ["20260530", "20260531"]

# ── 텔레그램 ───────────────────────────────────────────
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID   = os.environ["CHAT_ID"]

# ── 헤더 (없으면 403) ──────────────────────────────────
HEADERS = {
    "sec-ch-ua-platform": '"macOS"',
    "referer":            "https://tickets.interpark.com/",
    "user-agent":         "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "accept":             "application/json, text/plain, */*",
    "sec-ch-ua":          '"HeadlessChrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
    "accept-language":    "ko-KR",
    "sec-ch-ua-mobile":   "?0",
}

# ──────────────────────────────────────────────────────

def get_grade_map():
    """좌석 등급번호 → 등급명 딕셔너리 반환 예) {"1":"VIP석", "2":"R석"}"""
    url = f"{BASE_URL}/v1/goods/{GOODS_CODE}/bestprices/group"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        data = resp.json()
        grades = data.get("data", [])
        return {
            str(g.get("seatGrade")): g.get("seatGradeName", "?")
            for g in grades
            if g.get("seatGrade")
        }
    except Exception as e:
        print(f"[등급 조회 오류] {e}")
        return {}


def check_remain(play_date):
    """날짜별 잔여석 조회. 빈 리스트 = 매진, 항목 있으면 취소표"""
    url = f"{BASE_URL}/v1/goods/{GOODS_CODE}/playSeq/PlayDate/{play_date}/ALL"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        data = resp.json()
        return data.get("data", {}).get("remainSeat", [])
    except Exception as e:
        print(f"[잔여석 조회 오류 {play_date}] {e}")
        return None


def send_telegram(message):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": message},
        timeout=10,
    )


def main():
    grade_map = get_grade_map()
    print(f"등급 정보: {grade_map}")

    available_list = []

    for date in PLAY_DATES:
        remain = check_remain(date)
        formatted = f"{date[:4]}년 {date[4:6]}월 {date[6:]}일"

        if remain is None:
            print(f"[{formatted}] 조회 실패")
            continue

        print(f"[{formatted}] remainSeat: {remain}")

        if len(remain) > 0:
            seats_lines = []
            for r in remain:
                seat_grade    = str(r.get("seatGrade", ""))
                grade_name    = grade_map.get(seat_grade, r.get("seatGradeName", "?"))
                remain_cnt    = r.get("remainCnt", "?")
                play_seq_name = r.get("playSeqName", "")
                seats_lines.append(f"  ✅ {grade_name} - 잔여: {remain_cnt}석 ({play_seq_name})")

            available_list.append(f"📅 {formatted}\n" + "\n".join(seats_lines))

    if available_list:
        msg  = "🚨 인터파크 취소표 발생!\n"
        msg += "🎵 DxS ［소야곡］ ON STAGE - DAEGU\n\n"
        msg += "\n\n".join(available_list)
        msg += f"\n\n🔗 {PERF_URL}"
        send_telegram(msg)
        print("✅ 텔레그램 알림 전송 완료!")
    else:
        print("😔 모든 날짜 매진 상태")


if __name__ == "__main__":
    main()
