import argparse
import sys
from supabase_client import supabase
from routes.auth import make_email

def create_or_update_admin(username, password, role="admin"):
    email = make_email(username)
    
    try:
        # 1. Create the user in auth.users bypassing email confirmation
        print(f"Attempting to create user {username} ({email})...")
        res = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True
        })
        
        user_id = res.user.id
        
        # 2. Insert into public.users
        supabase.table("users").insert({
            "id": user_id,
            "username": username,
            "role": role
        }).execute()
        
        print(f"Successfully created user '{username}' with role '{role}'.")
        
    except Exception as e:
        error_msg = str(e)
        if "already registered" in error_msg.lower():
            print(f"User '{username}' already exists. We currently don't support updating passwords via this simple script. Please use the Supabase dashboard to update passwords.")
        else:
            print(f"Error creating user: {error_msg}")
            sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create an admin user in Supabase')
    parser.add_argument('username', help='Admin username')
    parser.add_argument('password', help='Admin password')
    parser.add_argument('--role', default='admin', help='Role to assign (default: admin)')
    args = parser.parse_args()
    create_or_update_admin(args.username, args.password, args.role)
