"""Order and payment routes."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.requests import Request
from sqlalchemy import select

from ..database import get_db
from ..dependencies import require_auth
from ..models import User, Order
from ..services.wechat_service import (
    CREDIT_PLANS,
    SUBSCRIPTION_PLANS,
    create_prepay_order,
    verify_pay_callback,
    make_jsapi_params,
)

router = APIRouter(prefix="/api", tags=["orders"])


@router.get("/orders/plans")
def get_plans():
    """Get available pricing plans."""
    return {
        "credits": CREDIT_PLANS,
        "subscriptions": SUBSCRIPTION_PLANS,
    }


@router.post("/orders/create")
async def create_order(
    plan_id: str,
    user: User = Depends(require_auth),
    db=Depends(get_db),
):
    """Create a new order and return payment info."""
    # Find the plan
    all_plans = CREDIT_PLANS + SUBSCRIPTION_PLANS
    plan = next((p for p in all_plans if p["id"] == plan_id), None)
    if not plan:
        raise HTTPException(status_code=400, detail="Invalid plan")

    order = Order(
        id=uuid.uuid4().hex[:16],
        user_id=user.id,
        type="credits" if plan in CREDIT_PLANS else "subscription",
        amount=plan["price_fen"],
        credits_amount=plan.get("credits"),
        description=plan["name"],
        status="pending",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # Call WeChat Pay unified order API
    # Use NATIVE for PC, JSAPI for in-WeChat
    trade_type = "NATIVE"
    try:
        result = await create_prepay_order(
            order_id=order.id,
            amount_fen=order.amount,
            description=order.description,
            trade_type=trade_type,
        )
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # Store prepay_id
    order.wechat_prepay_id = result.get("prepay_id", "")
    db.commit()

    response = {
        "order_id": order.id,
        "status": "pending",
        "amount": order.amount,
    }

    if trade_type == "NATIVE":
        response["qr_url"] = result.get("code_url", "")
    else:
        response["jsapi_params"] = make_jsapi_params(result.get("prepay_id", ""))

    return response


@router.get("/orders/{order_id}")
def get_order(order_id: str, user: User = Depends(require_auth), db=Depends(get_db)):
    """Get order status."""
    order = db.execute(
        select(Order).where(Order.id == order_id, Order.user_id == user.id)
    ).scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "id": order.id,
        "type": order.type,
        "amount": order.amount,
        "credits_amount": order.credits_amount,
        "description": order.description,
        "status": order.status,
        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
        "created_at": order.created_at.isoformat() if order.created_at else None,
    }


@router.get("/orders")
def list_orders(user: User = Depends(require_auth), db=Depends(get_db)):
    """List user's orders."""
    orders = db.execute(
        select(Order)
        .where(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
    ).scalars().all()
    return {"orders": [
        {
            "id": o.id,
            "type": o.type,
            "amount": o.amount,
            "credits_amount": o.credits_amount,
            "description": o.description,
            "status": o.status,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in orders
    ]}


@router.post("/payments/wechat/callback")
async def wechat_pay_callback(request: Request, db=Depends(get_db)):
    """WeChat Pay async callback endpoint."""
    body = await request.body()
    xml_str = body.decode("utf-8")

    try:
        data = verify_pay_callback(xml_str)
    except ValueError:
        return "<xml><return_code><![CDATA[FAIL]]></return_code></xml>"

    if data.get("result_code") != "SUCCESS":
        return "<xml><return_code><![CDATA[SUCCESS]]></return_code></xml>"

    order_id = data.get("out_trade_no")
    transaction_id = data.get("transaction_id")

    order = db.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()
    if not order or order.status == "paid":
        return "<xml><return_code><![CDATA[SUCCESS]]></return_code></xml>"

    # Update order
    order.status = "paid"
    order.wechat_transaction_id = transaction_id
    order.paid_at = datetime.now(timezone.utc)

    # Credit the user
    user = db.execute(select(User).where(User.id == order.user_id)).scalar_one_or_none()
    if user and order.type == "credits" and order.credits_amount:
        user.credits += order.credits_amount

    db.commit()

    return "<xml><return_code><![CDATA[SUCCESS]]></return_code></xml>"
