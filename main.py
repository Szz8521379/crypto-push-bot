import os
import requests
from bs4 import BeautifulSoup
import time

WEBHOOK = os.environ.get("WEBHOOK_NEWCOINS")
DEX_API = "https://api.dexscreener.com/latest/dex/pairs/solana"

def send_to_wechat(content: str):
    if not WEBHOOK:
        print("Error: WEBHOOK_NEWCOINS 未设置")
        return
    payload = {
        "msgtype": "text",
        "text": {"content": content}
    }
    try:
        res = requests.post(WEBHOOK, json=payload)
        print("推送状态码:", res.status_code)
        print("推送返回:", res.text)
    except Exception as e:
        print("推送失败:", e)

def fetch_dex_tokens():
    """从 DexScreener 获取符合条件的币"""
    try:
        res = requests.get(DEX_API, timeout=15)
        data = res.json()
        pairs = data.get("pairs", [])
        filtered = []
        for pair in pairs:
            # 过滤条件：Raydium DEX、minAge>=4h、min24HTxns>=1000、minLiq>=20,000 已内置dex筛选URL规则，API只取solana链
            base = pair.get("baseToken", {})
            fdv = pair.get("fdv") or 0
            vol_24h = pair.get("volume", {}).get("h24", 0)
            dex_ids = pair.get("dexId")
            pair_age = pair.get("age") or 0  # 单位小时
            # 过滤条件硬性加下，尽量匹配你给的网址要求
            if fdv >= 1_000_000 and vol_24h >= 1000 and pair_age >= 4 and dex_ids == "raydium":
                filtered.append({
                    "name": base.get("name"),
                    "symbol": base.get("symbol"),
                    "market_cap": fdv,
                    "volume_24h": vol_24h,
                    "pairAddress": pair.get("pairAddress"),
                    "url": pair.get("url"),
                })
        return filtered
    except Exception as e:
        print("获取DexScreener数据失败:", e)
        return []

def fetch_alva_info(token_name):
    """通过 alva.xyz 搜索代币，抓取简介、讨论度、大V（只抓第1条结果示例）"""
    search_url = f"https://alva.xyz/zh-CN/search?q={token_name}"
    try:
        res = requests.get(search_url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        # 找第一个代币简介
        intro_div = soup.find("div", class_="token-introduction")
        intro = intro_div.get_text(strip=True) if intro_div else "无简介"
        # 讨论度、热度示例（需要你确认网页结构，我用示意）
        hot_score_tag = soup.find("div", class_="hot-score")
        hot_score = hot_score_tag.get_text(strip=True) if hot_score_tag else "无"
        # 大V参与示例：找class包含“大V”的地方
        big_vs = []
        bigv_tags = soup.select("div.bigv-list span.name")
        for tag in bigv_tags:
            big_vs.append(tag.get_text(strip=True))
        bigv_str = ", ".join(big_vs) if big_vs else "无大V信息"
        return intro, hot_score, bigv_str
    except Exception as e:
        print(f"获取alva信息失败({token_name}):", e)
        return "无简介", "无", "无大V信息"

def main():
    tokens = fetch_dex_tokens()
    if not tokens:
        send_to_wechat("【提醒】今日无符合条件的新币。")
        return

    msg = "📢【Dex + Alva 新币监控】\n\n"
    for t in tokens[:5]:  # 限制推送5条，避免太长
        intro, hot_score, bigv_str = fetch_alva_info(t["name"])
        msg += (f"🚀 {t['symbol']} | 市值: {t['market_cap'] / 1e6:.2f}M | 24h交易量: {t['volume_24h']:.0f}\n"
                f"简介: {intro}\n"
                f"讨论度: {hot_score} | 大V: {bigv_str}\n"
                f"交易链接: {t['url']}\n\n")
        time.sleep(2)  # 休眠防止被封禁

    send_to_wechat(msg)

if __name__ == "__main__":
    main()
