import aiohttp
import logging

async def get_signal(symbol="BTCUSDT", interval="15m"):
    # Используем публичный API Binance (не требует ключей)
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=100"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return f"❌ Ошибка Binance API: {resp.status}"
                data = await resp.json()
    except Exception as e:
        return f"❌ Ошибка сети: {str(e)}"

    # Закрывающие цены
    closes = [float(candle[4]) for candle in data]
    
    # 1. Расчет EMA (9 и 21)
    def calc_ema(prices, period):
        multiplier = 2 / (period + 1)
        ema = prices[0]
        for price in prices[1:]:
            ema = (price - ema) * multiplier + ema
        return ema

    ema9 = calc_ema(closes, 9)
    ema21 = calc_ema(closes, 21)
    
    # 2. Расчет RSI (14)
    def calc_rsi(prices, period=14):
        gains, losses = [], []
        for i in range(1, len(prices)):
            diff = prices[i] - prices[i-1]
            if diff >= 0:
                gains.append(diff)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(diff))
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    rsi = calc_rsi(closes)
    current_price = closes[-1]

    # Логика сигнала
    signal = "НЕТ СИГНАЛА"
    confidence = 0
    
    if ema9 > ema21 and rsi < 70:
        signal = "📈 ПОКУПКА (LONG)"
        # Чем ниже RSI, тем выше уверенность
        confidence = round(70 + (50 - rsi) if rsi < 50 else 65, 1)
    elif ema9 < ema21 and rsi > 30:
        signal = "📉 ПРОДАЖА (SHORT)"
        confidence = round(70 + (rsi - 50) if rsi > 50 else 65, 1)
    
    text = (
        f"📊 <b>Анализ {symbol} ({interval})</b>\n\n"
        f"Цена: <code>{current_price:.2f}</code>\n"
        f"Тренд: {'Восходящий 🟢' if ema9 > ema21 else 'Нисходящий 🔴'}\n"
        f"RSI (14): <code>{rsi:.1f}</code>\n\n"
        f"<b>Сигнал: {signal}</b>\n"
        f"Уверенность: {confidence}%\n\n"
        f"<i>Анализ по алгоритму EMA+RSI. Не является финансовой рекомендацией.</i>"
    )
    return text
