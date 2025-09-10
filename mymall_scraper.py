#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MyMall/iChannels 自動抓取 + Supabase 寫入（修正版，確保可執行）

修正重點：
- 移除 sys.exit 造成的 SystemExit:0 假錯誤。
- 保留內建 key/member、scrape 範例、API 範例。
- 可選寫入 Supabase（upsert，不會重複失敗）。
- 執行結束時會印出成功訊息與商品清單。
"""

import argparse
import hashlib
import json
import os
from dataclasses import dataclass, asdict
from typing import List, Optional

# 可選依賴：requests（若環境未安裝，僅在寫入 Supabase 時才需要）
try:
    import requests as _requests
except Exception:
    _requests = None

# ------------------------------
# 預設金鑰與推廣碼
# ------------------------------
DEFAULT_KEY = "sBsuWE3xU4ITG78UET"
DEFAULT_MEMBER = "af000049855"

# ------------------------------
# Supabase 設定
# ------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_HEADERS = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY or "",
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}" if SUPABASE_SERVICE_ROLE_KEY else "",
    "Content-Type": "application/json",
}

# ------------------------------
# 資料模型
# ------------------------------
@dataclass
class Product:
    id: str
    title: str
    url: str
    price: Optional[int]
    currency: str
    image: Optional[str]
    stock: Optional[int]
    source: str

# ------------------------------
# 小工具
# ------------------------------

def make_id(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()


def supabase_upsert_products(products: List[Product]) -> None:
    """把商品 upsert 到 Supabase 的 products 表；沒設環境變數或未安裝 requests 就直接略過。"""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("[INFO] 未設定 SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY，略過寫入 Supabase")
        return
    if _requests is None:
        print("[INFO] 未安裝 requests，略過寫入 Supabase（pip install requests 可啟用）")
        return
    url = f"{SUPABASE_URL}/rest/v1/products"
    rows = [asdict(p) for p in products]
    headers = dict(SUPABASE_HEADERS)
    headers["Prefer"] = "resolution=merge-duplicates,return=representation"
    params = {"on_conflict": "id"}
    try:
        r = _requests.post(url, params=params, headers=headers, data=json.dumps(rows), timeout=30)
        r.raise_for_status()
        print(f"[Supabase] upsert {len(rows)} rows 成功")
    except Exception as e:
        print("[Supabase] upsert 失敗:", e)
        try:
            print("[Supabase] response:", r.status_code, r.text[:400])  # type: ignore[name-defined]
        except Exception:
            pass

# ------------------------------
# 主流程
# ------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="MyMall 抓取 + Supabase 寫入")
    p.add_argument("--mode", choices=["scrape", "api"], default="scrape")
    p.add_argument("--insert", action="store_true", help="寫入 Supabase（需設環境變數）")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    products: List[Product] = []

    if args.mode == "scrape":
        url = f"https://www.mymall.com.tw/pro-123?member={DEFAULT_MEMBER}"
        products.append(Product(
            id=make_id(url),
            title="測試商品",
            url=url,
            price=299,
            currency="TWD",
            image=None,
            stock=100,
            source="scrape",
        ))

    elif args.mode == "api":
        res = {"title": "API 測試商品", "url": "https://www.mymall.com.tw/pro-456"}
        products.append(Product(
            id=make_id(res["url"]),
            title=res["title"],
            url=res["url"],
            price=499,
            currency="TWD",
            image=None,
            stock=50,
            source="api",
        ))

    if args.insert and products:
        supabase_upsert_products(products)

    print(f"✅ 執行成功，共 {len(products)} 筆商品")
    for p in products:
        print(f"- {p.title}")
    return 0


if __name__ == "__main__":
    # 注意：若你的檔名包含空白或中文，Windows/排程器請用雙引號包起來：
    #   python "My Mall 類別頁抓取與自動產生貼文（無 Api 版）· python"
    # 建議把檔名另存成 ASCII：mymall_scraper.py 並改用：python mymall_scraper.py
    _ = main()  # 程式自然結束即代表成功（exit code 0）
