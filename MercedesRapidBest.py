import os
import sys
import re
import requests
from bs4 import BeautifulSoup
import time

# ================== НАСТРОЙКИ ==================
URL = "https://funpay.com/lots/3503/"
CHECK_INTERVAL = 8

# 🔐 Токен берется из переменных окружения Render
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    print("❌ КРИТИЧЕСКАЯ ОШИБКА: BOT_TOKEN не найден в переменных окружения!")
    print("👉 Добавь BOT_TOKEN в Environment Variables на Render")
    sys.exit(1)

# ✅ ID чатов можно оставить в коде (они не секретные)
CHAT_IDS = ["6066638745", "7930094492"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "ru-RU,ru;q=0.9",
}

# ================== БАН-СЛОВА ==================
BANNED_WORDS = [
    "index", "buy", "скупаю", "better",
    "лучше", "индексе", "best",
    "teg", "Tags", "теги", "lucky block", "индекс"
]

# ================== ТОВАРЫ =====================
ITEMS = {
    (
        "garama and madundung",
        "garama and madungdung",
        "гарама и мадундунг",
        "garama and madung",
    ): (100, 350),

    (
        "tictac sahur",
        "tic tac sahur",
        "тиктак сахур",
        "tiktak sahur",
        "tiktac sahur",
    ): (50, 150),

    (
        "ketupat kepat",
        "ketupat",
        "кетупат кепат",
    ): (50, 100),

    (
        "los primos",
        "лос примос",
    ): (80, 110),

    (
        "ketchuru and musturu",
        "кетчуру и мустуру",
    ): (79, 200),

    (
        "la secret combination",
        "ла секрет комбинация",
    ): (72, 250),

    (
        "my heart",
        "noo my heart",
    ): (15, 40),

    (
        "la taco combination",
        "ла тако комбинация",
        "la taco combinastion",
        "ла тако комбинасион",
        "tralaledon",
    ): (64, 200),

    (
        "La ginger sekolah",
        "нуклеаро динозавро",
        "nuclearo dinossaur",
    ): (35, 50),

    (
        "dragon canneloni",
    ): (1000, 3004),

    (
        "burguro and fryuro",
    ): (100, 600),

    (
        "fragrama and chocrama",
        "spooky and pumpky",
    ): (384, 599),

    (
        "reinito sleighito",
    ): (490, 504),

    (
        "capitano moby",
    ): (584, 705),
}

# ===============================================

session = requests.Session()
session.headers.update(HEADERS)
sent_links = set()

def send_telegram(text):
    """Отправка сообщения в Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    success = False
    
    for chat_id in CHAT_IDS:
        try:
            response = session.post(
                url,
                data={
                    "chat_id": chat_id,
                    "text": text,
                    "disable_web_page_preview": False
                },
                timeout=5
            )
            if response.status_code == 200:
                success = True
                print(f"✅ Отправлено в чат {chat_id}")
            else:
                print(f"❌ Ошибка Telegram: {response.status_code}")
        except Exception as e:
            print(f"❌ Ошибка отправки: {e}")
    
    return success

# ================== ОСНОВНОЙ ЦИКЛ ==================
print("🚀 FunPay Monitor запущен на Render!")
print(f"⏱️ Интервал проверки: {CHECK_INTERVAL} сек")
print(f"📦 Товаров в базе: {len(ITEMS)}")
print("=" * 50)

# Отправляем тестовое сообщение при запуске
send_telegram("✅ Бот запущен на Render и начал мониторинг!")

while True:
    start = time.time()

    try:
        r = session.get(URL, timeout=6)
        soup = BeautifulSoup(r.text, "html.parser")
        lots = soup.select("a.tc-item")

        market = {}

        # ---------- СБОР РЫНКА ----------
        for lot in lots:
            title_el = lot.select_one(".tc-desc-text")
            price_el = lot.select_one(".tc-price[data-s]")

            if not title_el or not price_el:
                continue

            title = title_el.get_text(strip=True)
            title_lower = title.lower()

            if any(bad in title_lower for bad in BANNED_WORDS):
                continue

            price = float(price_el["data-s"])
            link = lot.get("href")
            if not link.startswith("http"):
                link = "https://funpay.com" + link

            for keywords in ITEMS:
                if any(k in title_lower for k in keywords):
                    market.setdefault(keywords, []).append((price, link, title))

        for k in market:
            market[k].sort(key=lambda x: x[0])

        # ---------- TG ----------
        for keywords, (min_p, max_p) in ITEMS.items():
            if keywords not in market:
                continue

            lots_list = market[keywords]
            cheapest_price, cheapest_link, cheapest_title = lots_list[0]

            if cheapest_link in sent_links:
                continue

            if not (min_p <= cheapest_price <= max_p):
                continue

            market_price = lots_list[1][0] if len(lots_list) >= 2 else cheapest_price

            net_market_price = round(market_price * 0.7984, 2)
            net_profit = round(net_market_price - cheapest_price, 2)
            percent = round((net_profit / cheapest_price) * 100, 2)

            if net_profit < 50:
                recommend = "НЕ РЕКОМЕНДУЕМ 🟥"
            elif net_profit >= 70:
                recommend = "РЕКОМЕНДУЕМ 🟩"
            else:
                recommend = "🟨 НЕИЗВЕСТНО 🟨"

            send_telegram(
                "🔥 НАЙДЕН ТОВАР 🔥\n\n"
                f"📦 {cheapest_title}\n\n"
                f"🟢 Цена: {cheapest_price} ₽\n"
                f"🔵 Рынок: {market_price} ₽\n"
                f"🟡 После комиссии: {net_market_price} ₽\n\n"
                f"💰 Чистый профит: {net_profit} ₽ ({percent}%)\n\n"
                f"🔗 {cheapest_link}\n\n"
                f"{recommend}"
            )

            sent_links.add(cheapest_link)

        elapsed = round(time.time() - start, 2)
        print(f"⏱️ Проверка #{len(sent_links)}: {elapsed} сек | Найдено: {len(market)} товаров")

    except Exception as e:
        print("❌ Ошибка:", e)

    time.sleep(CHECK_INTERVAL)
