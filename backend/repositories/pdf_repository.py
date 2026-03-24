from supabase_client import supabase

def get_pdf_count_for_user(user_id: str) -> int:
    """
    Count the total number of PDFs uploaded by a user.
    """
    try:
        response = supabase.table("pdf_documents").select("id", count="exact").eq("user_id", user_id).execute()
        return response.count if response.count is not None else len(response.data)
    except Exception as e:
        raise Exception(f"Failed to count PDFs for user {user_id}: {str(e)}")

def save_pdf_record(user_id: str, file_name: str, storage_path: str) -> dict:
    """
    Insert a record of a newly uploaded PDF document into the database.
    """
    try:
        data = {
            "user_id": user_id,
            "file_name": file_name,
            "storage_path": storage_path
        }
        response = supabase.table("pdf_documents").insert(data).execute()
        return response.data[0] if response.data else {}
    except Exception as e:
        raise Exception(f"Failed to save PDF record for user {user_id}: {str(e)}")

def get_all_pdfs_for_user(user_id: str) -> list:
    """
    Retrieve all metadata about PDF records uploaded by a user from the database.
    """
    try:
        response = supabase.table("pdf_documents").select("*").eq("user_id", user_id).execute()
        return response.data
    except Exception as e:
        raise Exception(f"Failed to fetch PDFs for user {user_id}: {str(e)}")
