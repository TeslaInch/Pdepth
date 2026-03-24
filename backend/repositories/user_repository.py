from supabase_client import supabase

def get_user_by_id(user_id: str) -> dict:
    """
    Retrieve a user payload by their UUID.
    """
    try:
        response = supabase.table("users").select("*").eq("id", user_id).execute()
        return response.data[0] if response.data else {}
    except Exception as e:
        raise Exception(f"Failed to fetch user {user_id}: {str(e)}")

def create_user(user_id: str, email: str) -> dict:
    """
    Create a new user record in the users table.
    """
    try:
        data = {"id": user_id, "email": email}
        response = supabase.table("users").insert(data).execute()
        return response.data[0] if response.data else {}
    except Exception as e:
        raise Exception(f"Failed to create user {user_id}: {str(e)}")

def get_user_plan(user_id: str) -> str:
    """
    Retrieve the subscription plan for a user. Defaults to 'free'.
    """
    try:
        response = supabase.table("users").select("plan").eq("id", user_id).execute()
        return response.data[0].get("plan", "free") if response.data else "free"
    except Exception as e:
        raise Exception(f"Failed to fetch plan for user {user_id}: {str(e)}")

def update_user_plan(user_id: str, plan: str, stripe_customer_id: str) -> dict:
    """
    Update a user's subscription plan and Stripe customer ID.
    """
    try:
        data = {"plan": plan, "stripe_customer_id": stripe_customer_id}
        response = supabase.table("users").update(data).eq("id", user_id).execute()
        return response.data[0] if response.data else {}
    except Exception as e:
        raise Exception(f"Failed to update plan for user {user_id}: {str(e)}")
