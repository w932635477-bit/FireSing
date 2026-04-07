"""WeChat API service: login (OAuth) + payment (Native/JSAPI)."""

import hashlib
import time
import uuid
import xml.etree.ElementTree as ET
from typing import Optional

import httpx

from ..config import (
    WECHAT_OPEN_APP_ID,
    WECHAT_OPEN_APP_SECRET,
    WECHAT_MP_APP_ID,
    WECHAT_MP_APP_SECRET,
    WECHAT_PAY_MCH_ID,
    WECHAT_PAY_API_KEY,
    WECHAT_PAY_NOTIFY_URL,
)


# --- WeChat OAuth (Login) ---

def get_qr_login_url(state: str) -> str:
    """Generate QR code login URL for WeChat Open Platform."""
    return (
        f"https://open.weixin.qq.com/connect/qrconnect"
        f"?appid={WECHAT_OPEN_APP_ID}"
        f"&redirect_uri=https://firesing.cn/api/auth/callback"
        f"&response_type=code"
        f"&scope=snsapi_login"
        f"&state={state}#wechat_redirect"
    )


def get_mp_authorize_url(state: str) -> str:
    """Generate OAuth URL for WeChat Official Account (in-app)."""
    import urllib.parse
    redirect = urllib.parse.quote("https://firesing.cn/api/auth/callback", safe="")
    return (
        f"https://open.weixin.qq.com/connect/oauth2/authorize"
        f"?appid={WECHAT_MP_APP_ID}"
        f"&redirect_uri={redirect}"
        f"&response_type=code"
        f"&scope=snsapi_userinfo"
        f"&state={state}#wechat_redirect"
    )


async def exchange_code_for_userinfo(code: str, is_mp: bool = False) -> dict:
    """Exchange auth code for access_token, then get user info.

    For Open Platform (QR scan): uses WECHAT_OPEN_APP_ID.
    For Official Account (MP): uses WECHAT_MP_APP_ID.
    """
    if is_mp:
        app_id = WECHAT_MP_APP_ID
        app_secret = WECHAT_MP_APP_SECRET
    else:
        app_id = WECHAT_OPEN_APP_ID
        app_secret = WECHAT_OPEN_APP_SECRET

    # Step 1: code → access_token + openid
    token_url = "https://api.weixin.qq.com/sns/oauth2/access_token"
    params = {
        "appid": app_id,
        "secret": app_secret,
        "code": code,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(token_url, params=params)
        data = resp.json()

    if "errcode" in data:
        raise ValueError(f"WeChat OAuth error: {data.get('errmsg', data)}")

    access_token = data["access_token"]
    openid = data["openid"]
    unionid = data.get("unionid")

    # Step 2: access_token → user info
    userinfo_url = "https://api.weixin.qq.com/sns/userinfo"
    params = {
        "access_token": access_token,
        "openid": openid,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(userinfo_url, params=params)
        user_data = resp.json()

    return {
        "openid": openid,
        "unionid": unionid,
        "nickname": user_data.get("nickname", ""),
        "avatar_url": user_data.get("headimgurl", ""),
    }


# --- WeChat Pay (Native + JSAPI) ---

def _make_sign(params: dict) -> str:
    """Generate WeChat Pay signature."""
    sorted_params = sorted(params.items())
    sign_str = "&".join(f"{k}={v}" for k, v in sorted_params if v)
    sign_str += f"&key={WECHAT_PAY_API_KEY}"
    return hashlib.md5(sign_str.encode()).hexdigest().upper()


def _build_xml(params: dict) -> str:
    """Build XML for WeChat Pay API."""
    xml_parts = ["<xml>"]
    for k, v in params.items():
        xml_parts.append(f"<{k}><![CDATA[{v}]]></{k}>")
    xml_parts.append(f"<sign><![CDATA[{params['sign']}]]></sign>")
    xml_parts.append("</xml>")
    return "".join(xml_parts)


def _parse_xml(xml_str: str) -> dict:
    """Parse WeChat Pay XML response."""
    root = ET.fromstring(xml_str)
    return {child.tag: child.text for child in root}


async def create_prepay_order(
    order_id: str,
    amount_fen: int,
    description: str,
    trade_type: str = "NATIVE",
    openid: Optional[str] = None,
) -> dict:
    """Call WeChat unified order API.

    trade_type: "NATIVE" for QR code payment, "JSAPI" for in-WeChat payment.
    For JSAPI, openid is required.
    """
    nonce_str = uuid.uuid4().hex
    params = {
        "appid": WECHAT_OPEN_APP_ID or WECHAT_MP_APP_ID,
        "mch_id": WECHAT_PAY_MCH_ID,
        "nonce_str": nonce_str,
        "body": description,
        "out_trade_no": order_id,
        "total_fee": str(amount_fen),
        "spbill_create_ip": "119.28.134.124",
        "notify_url": WECHAT_PAY_NOTIFY_URL,
        "trade_type": trade_type,
    }
    if openid and trade_type == "JSAPI":
        params["openid"] = openid

    params["sign"] = _make_sign(params)
    xml_body = _build_xml(params)

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.mch.weixin.qq.com/pay/unifiedorder",
            content=xml_body,
            headers={"Content-Type": "application/xml"},
        )
        result = _parse_xml(resp.text)

    if result.get("return_code") != "SUCCESS" or result.get("result_code") != "SUCCESS":
        raise ValueError(f"WeChat Pay error: {result.get('return_msg', result)}")

    return result


def verify_pay_callback(xml_body: str) -> dict:
    """Verify and parse WeChat Pay callback XML."""
    data = _parse_xml(xml_body)

    # Verify signature
    sign = data.pop("sign", None)
    expected_sign = _make_sign(data)
    if sign != expected_sign:
        raise ValueError("Invalid WeChat Pay callback signature")

    return data


def make_jsapi_params(prepay_id: str) -> dict:
    """Generate JSAPI payment parameters for frontend."""
    nonce_str = uuid.uuid4().hex
    timestamp = str(int(time.time()))
    app_id = WECHAT_OPEN_APP_ID or WECHAT_MP_APP_ID

    params = {
        "appId": app_id,
        "timeStamp": timestamp,
        "nonceStr": nonce_str,
        "package": f"prepay_id={prepay_id}",
        "signType": "MD5",
    }
    params["paySign"] = _make_sign(params)
    return params


# --- Pricing Plans ---

CREDIT_PLANS = [
    {"id": "single", "credits": 1, "price_fen": 200, "name": "单首购买", "desc": "1 首"},
    {"id": "pack10", "credits": 10, "price_fen": 1500, "name": "10 首套餐", "desc": "10 首（7.5 折）"},
    {"id": "pack50", "credits": 50, "price_fen": 6000, "name": "50 首套餐", "desc": "50 首（6 折）"},
]

SUBSCRIPTION_PLANS = [
    {"id": "monthly", "price_fen": 2900, "name": "月度会员", "desc": "29 元/月，不限次数"},
]
