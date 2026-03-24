import os
import stripe
from repositories.user_repository import update_user_plan
import logging

logger = logging.getLogger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

def create_checkout_session(user: dict) -> str:
    """
    Creates a Stripe Checkout Session for the user to upgrade to standard paid plan.
    """
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=user.get("email"),
            client_reference_id=user.get("id"),
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Pdepth Paid Plan',
                    },
                    'unit_amount': 999, # e.g. $9.99
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=os.getenv("FRONTEND_URL", "http://localhost:3000") + '/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=os.getenv("FRONTEND_URL", "http://localhost:3000") + '/cancel',
        )
        return session.url
    except Exception as e:
        logger.error(f"Error creating Stripe checkout session: {e}", exc_info=True)
        raise e

def handle_webhook(payload: bytes, sig_header: str):
    """
    Handles the Stripe Webhook to upgrade the user's plan securely on completion.
    """
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        raise Exception(f"Invalid payload: {e}")
    except stripe.error.SignatureVerificationError as e:
        raise Exception(f"Invalid stripe signature: {e}")

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        user_id = session.get("client_reference_id")
        stripe_customer_id = session.get("customer")
        
        if user_id:
            logger.info(f"💰 Stripe Checkout completed for user {user_id}. Upgrading plan.")
            update_user_plan(user_id=user_id, plan="paid", stripe_customer_id=stripe_customer_id)
        else:
            logger.warning("Checkout session completed but missing client_reference_id.")
            
    return True
