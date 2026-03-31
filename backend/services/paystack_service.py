import os
import httpx
import hmac
import hashlib
import logging
from repositories.user_repository import update_user_plan

logger = logging.getLogger(__name__)

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")

async def initialize_transaction(user: dict) -> str:
    """
    Initializes a Paystack transaction to upgrade the user to the paid plan.
    Returns the authorization URL to redirect the user to.
    """
    if not PAYSTACK_SECRET_KEY:
        raise ValueError("PAYSTACK_SECRET_KEY is missing from environment variables.")

    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Amount is in kobo (100 kobo = 1 NGN).
    # Since PDepth was $9.99, let's keep it abstract, 99900 kobo usually means 999.00 local currency.
    payload = {
        "email": user.get("email"),
        "amount": 99900,
        "reference": f"{user.get('id')}_{os.urandom(4).hex()}",
        "callback_url": f"{frontend_url}/success",
        "metadata": {
            "custom_fields": [
                {
                    "display_name": "User ID",
                    "variable_name": "user_id",
                    "value": user.get("id")
                }
            ]
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            if data.get("status"):
                return data["data"]["authorization_url"]
            else:
                raise Exception(f"Paystack initialization failed: {data.get('message')}")
        except httpx.HTTPError as e:
            logger.error(f"HTTP Error during Paystack initialization: {e}", exc_info=True)
            raise Exception("Failed to connect to payment integration.")
        except Exception as e:
            logger.error(f"Error initializing Paystack transaction: {e}", exc_info=True)
            raise e

async def verify_paystack_transaction(reference: str, user_id: str) -> bool:
    """
    Actively verifying external transaction from Paystack directly via their API,
    and updates the database if successful.
    """
    if not PAYSTACK_SECRET_KEY:
        raise ValueError("PAYSTACK_SECRET_KEY missing")

    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            data = response.json()
            if data.get("status") and data.get("data", {}).get("status") == "success":
                # Valid transaction, lets upgrade the planner
                paystack_customer_id = data["data"].get("customer", {}).get("customer_code", "")
                
                logger.info(f"✅ Paystack Verify explicitly matched for user_id {user_id}. Paid tier activated.")
                update_user_plan(user_id=user_id, plan="paid", paystack_customer_id=paystack_customer_id)
                return True
            else:
                logger.warning(f"❌ Paystack verification failed. Payload: {data.get('data', {}).get('status')}")
                return False
        except httpx.HTTPError as e:
            logger.error(f"HTTP Verification failed: {e}")
            raise Exception("Payment verification server error.")
        except Exception as e:
            logger.error(f"Verify generic fail: {e}")
            raise e

def handle_webhook(payload: bytes, sig_header: str) -> bool:
    """
    Handles the Paystack webhook dynamically and verifies HMAC-SHA512.
    Upgrades the logic of the user plan securely.
    """
    if not PAYSTACK_SECRET_KEY:
        logger.error("PAYSTACK_SECRET_KEY is missing. Webhook operation aborted.")
        return False
        
    # Verify the signature
    expected_digest = hmac.new(
        PAYSTACK_SECRET_KEY.encode('utf-8'),
        payload,
        hashlib.sha512
    ).hexdigest()

    if expected_digest != sig_header:
        logger.warning(f"Invalid Paystack signature. Expected {expected_digest}, got {sig_header}")
        raise Exception("Invalid Paystack signature.")

    try:
        import json
        event = json.loads(payload.decode('utf-8'))
    except Exception as e:
        raise Exception(f"Invalid JSON payload: {e}")

    # Handle the charge.success event
    if event.get('event') == 'charge.success':
        event_data = event.get('data', {})
        
        metadata = event_data.get('metadata', {})
        # Protective check: Sometimes payload stringifies custom fields
        import json as builtin_json
        if isinstance(metadata, str):
            try:
                metadata = builtin_json.loads(metadata)
            except Exception:
                pass

        user_id = None
        
        # Extract user_id from metadata
        if metadata and isinstance(metadata, dict) and 'custom_fields' in metadata:
            for field in metadata['custom_fields']:
                if field.get('variable_name') == 'user_id':
                    user_id = field.get('value')
                    break
                    
        paystack_customer_id = event_data.get('customer', {}).get('customer_code', '')
        
        if user_id:
            logger.info(f"💰 Paystack Transaction completed for user {user_id}. Upgrading plan.")
            update_user_plan(user_id=user_id, plan="paid", paystack_customer_id=paystack_customer_id)
        else:
            logger.warning("Paystack charge success but missing user_id in metadata.")
            
    return True
