#!/usr/bin/env python3
"""
Lấy commission sản phẩm từ Shopee Affiliate bằng cookie đã export.

Cài đặt:
    pip install requests

Ví dụ:
    python shopee_affiliate_commission.py 26150541698 \
        --cookies affiliate.shopee.vn_28-07-2026.json

Nếu request tối giản bị 403, truyền các header động qua biến môi trường:
    Windows PowerShell:
        $env:SHOPEE_AF_AC_ENC_DAT="..."
        $env:SHOPEE_AF_AC_ENC_SZ_TOKEN="..."
        $env:SHOPEE_X_SAP_RI="..."
        $env:SHOPEE_X_SAP_SEC="..."

    Sau đó chạy lại lệnh phía trên.

Không hardcode hoặc commit cookie/token lên Git.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests


API_URL = "https://affiliate.shopee.vn/api/v3/offer/product"
PRICE_SCALE = 100_000
RATE_SCALE = 100_000


class ShopeeAffiliateError(RuntimeError):
    pass


def extract_item_id(value: str) -> str:
    """Nhận item_id trực tiếp hoặc URL sản phẩm Shopee."""
    value = value.strip()

    if value.isdigit():
        return value

    parsed = urlparse(value)
    path = parsed.path.rstrip("/")

    patterns = (
        r"/product/\d+/(\d+)$",
        r"-i\.\d+\.(\d+)$",
        r"/product_offer/(\d+)$",
    )

    for pattern in patterns:
        match = re.search(pattern, path)
        if match:
            return match.group(1)

    raise ValueError(f"Không tìm thấy item_id trong: {value}")


def load_session(cookie_file: Path) -> requests.Session:
    if not cookie_file.is_file():
        raise FileNotFoundError(f"Không tìm thấy file cookie: {cookie_file}")

    raw = json.loads(cookie_file.read_text(encoding="utf-8"))
    cookies = raw.get("cookies")

    if not isinstance(cookies, list):
        raise ValueError("JSON phải chứa trường 'cookies' dạng danh sách")

    session = requests.Session()

    for cookie in cookies:
        name = cookie.get("name")
        value = cookie.get("value")
        if not name or value is None:
            continue

        domain = cookie.get("domain")
        path = cookie.get("path", "/")

        if domain:
            session.cookies.set(name, value, domain=domain, path=path)
        else:
            session.cookies.set(name, value, path=path)

    return session


def build_headers(item_id: str) -> dict[str, str]:
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en,en-US;q=0.9,vi;q=0.8",
        "Affiliate-Program-Type": "1",
        "Referer": (
            "https://affiliate.shopee.vn/"
            f"offer/product_offer/{item_id}"
        ),
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/150.0.0.0 Safari/537.36"
        ),
        "X-SZ-SDK-Version": "1.12.21",
    }

    optional_dynamic_headers = {
        "af-ac-enc-dat": os.getenv("SHOPEE_AF_AC_ENC_DAT"),
        "af-ac-enc-sz-token": os.getenv("SHOPEE_AF_AC_ENC_SZ_TOKEN"),
        "x-sap-ri": os.getenv("SHOPEE_X_SAP_RI"),
        "x-sap-sec": os.getenv("SHOPEE_X_SAP_SEC"),
    }

    headers.update(
        {
            name: value
            for name, value in optional_dynamic_headers.items()
            if value
        }
    )

    return headers


def request_product(
    session: requests.Session,
    item_id: str,
    timeout: float = 30,
) -> dict[str, Any]:
    response = session.get(
        API_URL,
        params={"item_id": item_id},
        headers=build_headers(item_id),
        timeout=timeout,
    )

    content_type = response.headers.get("content-type", "")

    if response.status_code in {401, 403}:
        raise ShopeeAffiliateError(
            f"HTTP {response.status_code}: phiên cookie hết hạn hoặc request "
            "thiếu các header động af-ac/x-sap. Hãy copy header mới từ DevTools."
        )

    if response.status_code == 429:
        raise ShopeeAffiliateError(
            "HTTP 429: gọi quá nhanh. Hãy giảm tốc độ và thêm cache."
        )

    response.raise_for_status()

    if "application/json" not in content_type:
        preview = response.text[:300].replace("\n", " ")
        raise ShopeeAffiliateError(
            f"Response không phải JSON ({content_type!r}): {preview}"
        )

    payload = response.json()

    if payload.get("code") != 0:
        raise ShopeeAffiliateError(
            f"Shopee API lỗi: code={payload.get('code')}, "
            f"msg={payload.get('msg')!r}"
        )

    data = payload.get("data")
    if not isinstance(data, dict):
        raise ShopeeAffiliateError("Response không có object 'data'")

    return data


def raw_price_to_vnd(value: Any) -> float | None:
    try:
        return int(value) / PRICE_SCALE
    except (TypeError, ValueError):
        return None


def raw_rate_to_percent(value: Any) -> float | None:
    try:
        return int(value) / 1_000
    except (TypeError, ValueError):
        return None


def summarize(data: dict[str, Any]) -> dict[str, Any]:
    rate_text = data.get("commission_rate") or {}
    rate_raw = data.get("commission_rate_detail") or {}
    product = data.get("batch_item_for_item_card_full") or {}

    price_min_vnd = raw_price_to_vnd(product.get("price_min"))
    total_rate_raw = rate_raw.get("default_commission_rate")

    estimated_from_raw = None
    if price_min_vnd is not None and total_rate_raw is not None:
        estimated_from_raw = round(
            price_min_vnd * int(total_rate_raw) / RATE_SCALE
        )

    return {
        "item_id": data.get("item_id"),
        "shop_id": product.get("shopid"),
        "product_name": product.get("name"),
        "product_link": data.get("product_link"),
        "affiliate_link": data.get("long_link"),
        "price_min_vnd": price_min_vnd,
        "display_commission": data.get("commission"),
        "total_rate": rate_text.get("default_commission_rate"),
        "seller_rate": rate_text.get("seller_commission_rate"),
        "shopee_rate": rate_text.get("shopee_commission_rate"),
        "commission_cap": rate_text.get("commission_cap"),
        "total_rate_percent_raw": raw_rate_to_percent(total_rate_raw),
        "estimated_commission_vnd": estimated_from_raw,
        "is_capped": rate_text.get("is_capped"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Lấy commission sản phẩm từ Shopee Affiliate"
    )
    parser.add_argument(
        "product",
        help="item_id hoặc URL sản phẩm Shopee",
    )
    parser.add_argument(
        "--cookies",
        type=Path,
        default=Path("affiliate.shopee.vn_28-07-2026.json"),
        help="Đường dẫn file cookie JSON",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="In toàn bộ JSON response",
    )
    args = parser.parse_args()

    try:
        item_id = extract_item_id(args.product)
        session = load_session(args.cookies)
        data = request_product(session, item_id)

        result = data if args.raw else summarize(data)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    except (
        FileNotFoundError,
        ValueError,
        requests.RequestException,
        ShopeeAffiliateError,
    ) as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
