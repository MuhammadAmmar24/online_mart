from fastapi import HTTPException
import httpx
import json
import logging

from app import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def kong_jwt_token(email: str, id: str):
    try:
        # Create consumer in Kong
        await create_consumer_in_kong(email, id)
        # Create JWT credential in Kong
        await create_jwt_credential_in_kong(email, id)
    except Exception as e:
        logger.error(f"Error during Kong JWT token creation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def create_consumer_in_kong(email: str, custom_id: str):
    logger.info(f"Creating consumer in Kong with custom_id: {custom_id}")

    headers = {'Content-Type': 'application/json'}
    data = {
        "username": email,
        "custom_id": custom_id
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{settings.KONG_ADMIN_URL}/consumers", headers=headers, data=json.dumps(data))
        
        if response.status_code == 201:
            logger.info(f"Consumer created in Kong with custom_id: {custom_id}")
            return response.json()
        else:
            logger.error(f"Error creating consumer in Kong: {response.text} (Status code: {response.status_code})")
            raise HTTPException(status_code=response.status_code, detail=f"Error creating consumer in Kong: {response.text}")
    
    except httpx.RequestError as exc:
        logger.error(f"An error occurred while requesting Kong: {exc}")
        raise HTTPException(status_code=500, detail=f"Error creating consumer in Kong: {exc}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")




async def create_jwt_credential_in_kong(email: str, key: str):
    logger.info(f"Creating JWT credential in Kong for consumer: {email}")

    headers = {'Content-Type': 'application/json'}
    data = {
        "key": key
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{settings.KONG_ADMIN_URL}/consumers/{email}/jwt", headers=headers, data=json.dumps(data))
        
        if response.status_code == 201:
            logger.info(f"JWT credential created in Kong for consumer: {email}")
            return response.json()
        else:
            logger.error(f"Error creating JWT credential in Kong: {response.text} (Status code: {response.status_code})")
            raise HTTPException(status_code=response.status_code, detail=f"Error creating JWT credential in Kong: {response.text}")
    
    except httpx.RequestError as exc:
        logger.error(f"An error occurred while requesting Kong: {exc}")
        raise HTTPException(status_code=500, detail=f"Error creating JWT credential in Kong: {exc}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
