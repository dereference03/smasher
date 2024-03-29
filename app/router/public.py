from fastapi import APIRouter, Depends, BackgroundTasks
from app.internal import storage, sms_handler
import random
from redis import Redis
from app import config
from . import schemas


router = APIRouter(prefix="/public", tags=["Smsher"])


@router.post("/sms", response_model=schemas.SmsResponse)
async def send_sms(
    phoneNumber: str,
    background_tasks: BackgroundTasks,
    redis_client: Redis = Depends(storage.get_redis),
):
    otp = redis_client.get(phoneNumber)
    if otp:
        otp = random.randint(0000, 9999)
        background_tasks.add_task(
            sms_handler.send_otp, phoneNumber, config.MESSAGE_TEMPLATE.format(otp=otp)
        )

        await redis_client.set(phoneNumber, otp, ex=config.OTP_TIMEOUT)

    return {"phone": phoneNumber, "otp": otp}


@router.post("/verify", response_model=None)
async def verify_otp(
    phoneNumber: str, otp: int, redis_client: Redis = Depends(storage.get_redis)
):
    value = await redis_client.get(phoneNumber)
    if value:
        if otp == int(value):
            return {"status": "verified"}
    return {"status": "not verified"}
