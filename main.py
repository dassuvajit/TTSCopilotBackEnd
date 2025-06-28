from fastapi import FastAPI, HTTPException, Depends, Form
from fastapi.security import OAuth2PasswordRequestForm
from utils import (
    get_supabase, get_user_by_username, verify_password,
    create_token, get_current_user, get_user_version, generate_signed_url
)
from datetime import datetime
app = FastAPI()

@app.post("/token")
def login(
    username: str = Form(...),
    password: str = Form(...),
    device_id: str = Form(...)
):
    client = get_supabase()

    # 1️⃣ Get user from DB
    user = get_user_by_username(client, username)
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    # 2️⃣ Check license expiry
    expiry_str = user.get("expiry_date")
    if expiry_str:
        expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
        if datetime.now().date() > expiry_date:
            raise HTTPException(status_code=403, detail="❌ License has expired. Please renew.")

    # 3️⃣ Check device lock
    saved_device_id = user.get("device_info")
    if saved_device_id is None:
        client.table("users").update({"device_info": device_id}).eq("id", user["id"]).execute()
    elif saved_device_id != device_id:
        raise HTTPException(status_code=403, detail="❌ This account is locked to another device.")

    # 4️⃣ All good → generate token
    token = create_token({"sub": user["username"]})
    return {"access_token": token, "token_type": "bearer"}




from utils import generate_signed_url
from utils import encrypt_url

@app.get("/check-update")
def check_update(current_user=Depends(get_current_user)):
    try:
        client = get_supabase()
        print("🧠 Logged in user:", current_user)

        version = get_user_version(client)
        print("📦 Version data:", version)

        if not version:
            raise HTTPException(status_code=404, detail="No version assigned")

        signed_url = generate_signed_url(client, version["file_url"])
        encrypted_url = encrypt_url(signed_url)

        return {
            "version": version["version"],
            "download_url": encrypted_url
        }

    except Exception as e:
        print("🔥 Error in /check-update:", e)
        raise HTTPException(status_code=500, detail="Something went wrong")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
