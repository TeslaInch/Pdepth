from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from supabase_client import supabase
from repositories.user_repository import get_user_by_id, create_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    FastAPI dependency that:
    1. Verifies the JWT via Supabase Auth
    2. Extracts the user ID and Email
    3. Fetches the user record from the UserRepository
    4. Auto-creates the user record in the DB if it doesn't exist
    """
    try:
        # 1. Decode/verify JWT using Supabase Auth
        auth_response = supabase.auth.get_user(token)
        
        # In supabase-py, auth_response contains a user object (UserResponse)
        if not auth_response or not getattr(auth_response, 'user', None):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
            
        # 2. Extract user_id and email
        user_id = auth_response.user.id
        email = auth_response.user.email
        
        # 3. Call UserRepository
        user_record = get_user_by_id(user_id)
        
        # 4. Auto-create if not exists
        if not user_record:
            user_record = create_user(user_id=user_id, email=email)
            
        # 5. Return user dict
        return user_record

    except Exception as e:
        # Catch any parsing or supabase auth errors
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
