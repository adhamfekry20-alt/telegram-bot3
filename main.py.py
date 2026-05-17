import ccxt
import pandas as pd
import pandas_ta as ta
import time
import requests

# ==========================================
# 1. إعدادات تيليجرام (قم بوضع بياناتك هنا)
# ==========================================
TELEGRAM_TOKEN = 'ضع_التوكن_الخاص_بك_هنا'
TELEGRAM_CHAT_ID = 'ضع_أيدي_القناة_هنا' # سنشرح لك لاحقاً كيف تحضره إذا لم تكن تعرفه

def send_telegram_message(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("خطأ في إرسال التليجرام:", e)

# ==========================================
# 2. إعدادات استراتيجية الأزواج والأهداف
# ==========================================
exchange = ccxt.binance({'enableRateLimit': True})

pairs_config = {
    'BTC/USDT':  {'leverage': 150, 'tp_pct': 0.0133, 'sl_pct': 0.0066},
    'ETH/USDT':  {'leverage': 150, 'tp_pct': 0.0133, 'sl_pct': 0.0066},
    'BNB/USDT':  {'leverage': 100, 'tp_pct': 0.02,   'sl_pct': 0.01},
    'SOL/USDT':  {'leverage': 100, 'tp_pct': 0.02,   'sl_pct': 0.01},
    'XRP/USDT':  {'leverage': 100, 'tp_pct': 0.02,   'sl_pct': 0.01}
}

# تتبع الصفقات المفتوحة لكل زوج لمنع التكرار (القاعدة 5-4)
active_trades = {pair: None for pair in pairs_config}
daily_stats = {'won': 0, 'lost': 0}

# ==========================================
# 3. محرك التحليل الفني والذكاء (Technical Engine)
# ==========================================
def fetch_and_analyze(symbol):
    try:
        # جلب شموع 15 دقيقة (كمثال للتأكيد)
        bars = exchange.fetch_ohlcv(symbol, timeframe='15m', limit=100)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # 2-1: مؤشر MACD بالإعدادات الحساسة (3, 26, 1)
        macd = ta.macd(df['close'], fast=3, slow=26, signal=1)
        df = pd.concat([df, macd], axis=1)
        
        # 2-8: مؤشر RSI لمعرفة التشبع
        df['rsi'] = ta.rsi(df['close'], length=14)
        
        # استخراج البيانات الحالية
        current_close = df['close'].iloc[-1]
        current_rsi = df['rsi'].iloc[-1]
        macd_hist = df['MACDh_3_26_1'].iloc[-1]
        
        # توليد إشارة افتراضية بناءً على المعطيات (يمكن توسيعها للبرايس أكشن والسيولة)
        signal = None
        ai_score = 0
        
        if current_rsi < 30 and macd_hist > 0: # مثال: تشبع بيعي + بداية زخم إيجابي
            signal = 'LONG'
            ai_score = 88 # نسبة ذكاء اصطناعي افتراضية بناءً على قوة المعطيات
        elif current_rsi > 70 and macd_hist < 0:
            signal = 'SHORT'
            ai_score = 85
            
        return signal, current_close, ai_score
    except Exception as e:
        print(f"خطأ في تحليل {symbol}: {e}")
        return None, None, 0

# ==========================================
# 4. محرك التشغيل وإدارة الصفقات 24/7
# ==========================================
def main_loop():
    send_telegram_message("🚀 *تم تشغيل نظام Crypto Sniper AI بنجاح* 🚀\nيقوم الآن بمراقبة الأسواق طوال اليوم...")
    
    while True:
        for symbol, config in pairs_config.items():
            
            # --- أ. التحقق من الصفقات المفتوحة مسبقاً ---
            if active_trades[symbol] is not None:
                # جلب السعر المباشر لمعرفة هل ضربنا الهدف أم الوقف
                try:
                    ticker = exchange.fetch_ticker(symbol)
                    current_price = ticker['last']
                    trade = active_trades[symbol]
                    
                    if trade['type'] == 'LONG':
                        if current_price >= trade['tp']:
                            send_telegram_message(f"✅ *هدف محقق!*\nالزوج: {symbol}\nالنتيجة: ربح 200%")
                            active_trades[symbol] = None
                        elif current_price <= trade['sl']:
                            send_telegram_message(f"❌ *وقف خسارة!*\nالزوج: {symbol}\nالنتيجة: خسارة 100%")
                            active_trades[symbol] = None
                            
                    elif trade['type'] == 'SHORT':
                        if current_price <= trade['tp']:
                            send_telegram_message(f"✅ *هدف محقق!*\nالزوج: {symbol}\nالنتيجة: ربح 200%")
                            active_trades[symbol] = None
                        elif current_price >= trade['sl']:
                            send_telegram_message(f"❌ *وقف خسارة!*\nالزوج: {symbol}\nالنتيجة: خسارة 100%")
                            active_trades[symbol] = None
                except Exception as e:
                    pass
                continue # تخطي التحليل لهذا الزوج لأنه قيد التداول حالياً

            # --- ب. البحث عن فرص جديدة (إذا لم يكن هناك صفقة شغالة) ---
            signal, price, ai_score = fetch_and_analyze(symbol)
            
            if signal and ai_score >= 80: # الدخول فقط إذا كانت الفرصة قوية
                # حساب الأهداف بناءً على معادلاتك الدقيقة
                if signal == 'LONG':
                    tp = price * (1 + config['tp_pct'])
                    sl = price * (1 - config['sl_pct'])
                else: # SHORT
                    tp = price * (1 - config['tp_pct'])
                    sl = price * (1 + config['sl_pct'])
                
                # تسجيل الصفقة لتتبعها وعدم إرسالها مرة أخرى
                active_trades[symbol] = {
                    'type': signal, 'entry': price, 'tp': tp, 'sl': sl
                }
                
                # إرسال التوصية
                msg = f"""
🎯 *إشارة {signal} جديدة* (SCALP)
🪙 **الزوج:** {symbol}
🔥 **قوة الإشارة (AI):** {ai_score}%
💰 **سعر الدخول:** {price}
🚀 **الرافعة المالية:** {config['leverage']}x

✅ **الهدف (200%):** {round(tp, 4)}
❌ **وقف الخسارة (-100%):** {round(sl, 4)}

⏳ *يتم الآن متابعة الصفقة آلياً ولن يتم إرسال إشارة لهذا الزوج حتى تنتهي.*
"""
                send_telegram_message(msg)
                
        # انتظار لمدة دقيقة قبل مسح السوق مرة أخرى لتخفيف الضغط على الخوادم
        time.sleep(60)

if __name__ == "__main__":
    main_loop()