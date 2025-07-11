import os
import requests
from datetime import datetime, timedelta

WEBHOOK = os.environ.get("WEBHOOK_NEWCOINS")

def send_to_wechat(content: str):
    if not WEBHOOK:
        print("Webhook 未设置")
        return
    data = {
        "msgtype": "text",
        "text": {"content": content}
    }
    res = requests.post(WEBHOOK, json=data)
    print("推送状态:", res.status_code)
    print("内容:", res.text)

def fetch_pump():
    try:
        res = requests.get("https://pump.fun/api/trending", timeout=10)
        tokens = res.json()
        filtered = []
        for t in tokens:
            if t.get("marketCap", 0) >= 1_000_000:
                filtered.append(
                    f"🚀 {t.get('symbol')} 市值: {int(t['marketCap']/1e6)}M，交易量: {int(t.get('volume',0))}\n🔗 https://pump.fun/{t.get('tokenAddress')}"
                )
        return filtered
    except Exception as e:
        print("pump.fun 获取失败:", e)
        return []

def fetch_dex():
    try:
        res = requests.get("https://api.dexscreener.com/latest/dex/pairs/solana", timeout=10)
        now = datetime.utcnow()
        tokens = []
        for p in res.json().get("pairs", []):
            if not p.get("pairCreatedAt"): continue
            created = datetime.fromisoformat(p["pairCreatedAt"].replace("Z", "+00:00"))
            if now - created > timedelta(hours=24): continue
            if float(p.get("fdv", 0)) >= 1_000_000:
                tokens.append(
                    f"🔥 {p['baseToken']['symbol']} 市值: {int(float(p['fdv'])/1e6)}M，交易量: {int(p['volume']['h24'])}\n🔗 {p['url']}"
                )
        return tokens
    except Exception as e:
        print("dexscreener 获取失败:", e)
        return []

def main():
    pump_data = fetch_pump()
    dex_data = fetch_dex()

    content = "📊【加密新币推送】24小时内市值≥1M USDT\n\n"

    content += "🔹Pump:\n" + ("\n".join(pump_data[:5]) if pump_data else "暂无数据") + "\n\n"
    content += "🔹DexScreener:\n" + ("\n".join(dex_data[:5]) if dex_data else "暂无数据")

    send_to_wechat(content)

if __name__ == "__main__":
    main()
