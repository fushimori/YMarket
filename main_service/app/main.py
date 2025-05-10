# main_service/app/main.py
from fastapi import FastAPI, Request, Form, Depends, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uuid
import json
import time
import jwt
import httpx
import asyncio

app = FastAPI()

# Templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Service URLs
AUTH_SERVICE_URL = "http://auth_service:8001"
CATALOG_SERVICE_URL = "http://catalog_service:8003"
CART_SERVICE_URL = "http://cart_service:8004"
PAYMENT_SERVICE_URL = "http://payment_service:8005"

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

# HTTP client for making requests to other services
async def get_http_client():
    async with httpx.AsyncClient() as client:
        yield client

def decode_jwt(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        return email
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/", response_class=HTMLResponse)
async def read_home(request: Request):
    try:
        jwt_token = request.cookies.get("access_token")
        if jwt_token:
            email = decode_jwt(jwt_token)
        else:
            email = None
    except HTTPException as e:
        print(f"DEBUG main service: JWT error - {e.detail}")
        email = None
    print("DEBUG: main_service check cookies: email - ", email)

    return templates.TemplateResponse("index.html", {"request": request, "email": email})

@app.get("/profile", response_class=HTMLResponse)
async def get_profile(request: Request):
    jwt_token = request.cookies.get("access_token")
    
    if not jwt_token:
        print("DEBUG: No JWT token found in cookies")
        return RedirectResponse(url="/login", status_code=303)

    try:
        email = decode_jwt(jwt_token)
        if not email:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: email not found"
            )
        print(f"DEBUG: Decoded JWT token for email: {email}")
    except HTTPException as e:
        print(f"DEBUG: JWT decoding error: {e.detail}")
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse("profile.html", {"request": request, "email": email, "token": jwt_token})

@app.get("/cart", response_class=HTMLResponse)
async def get_cart(request: Request):
    jwt_token = request.cookies.get("access_token")
    
    if not jwt_token:
        print("DEBUG: No JWT token found in cookies")
        return RedirectResponse(url="/login", status_code=303)

    try:
        email = decode_jwt(jwt_token)
        if not email:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: email not found"
            )
        print(f"DEBUG: Decoded JWT token for email: {email}")
    except HTTPException as e:
        print(f"DEBUG: JWT decoding error: {e.detail}")
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse("cart.html", {"request": request, "email": email, "token": jwt_token})

@app.get("/wishlist", response_class=HTMLResponse)
async def get_wishlist(request: Request):
    jwt_token = request.cookies.get("access_token")
    
    if not jwt_token:
        print("DEBUG: No JWT token found in cookies")
        return RedirectResponse(url="/login", status_code=303)

    try:
        email = decode_jwt(jwt_token)
        if not email:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: email not found"
            )
        print(f"DEBUG: Decoded JWT token for email: {email}")
    except HTTPException as e:
        print(f"DEBUG: JWT decoding error: {e.detail}")
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse("wishlist.html", {"request": request, "email": email})

@app.get("/orders", response_class=HTMLResponse)
async def get_orders(request: Request):
    jwt_token = request.cookies.get("access_token")
    
    if not jwt_token:
        print("DEBUG: No JWT token found in cookies")
        return RedirectResponse(url="/login", status_code=303)

    try:
        email = decode_jwt(jwt_token)
        if not email:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: email not found"
            )
        print(f"DEBUG: Decoded JWT token for email: {email}")
    except HTTPException as e:
        print(f"DEBUG: JWT decoding error: {e.detail}")
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse("orders.html", {"request": request, "email": email})

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/product", response_class=HTMLResponse)
async def product(request: Request):
    jwt_token = request.cookies.get("access_token")
    return templates.TemplateResponse("product.html", {"request": request, "token": jwt_token})

@app.get("/signup", response_class=HTMLResponse)
async def signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/register")
async def register(request: Request, email: str = Form(...), password: str = Form(...), client: httpx.AsyncClient = Depends(get_http_client)):
    """Send a registration request to the auth service."""
    try:
        response = await client.post(
            f"{AUTH_SERVICE_URL}/register",
            json={"email": email, "password": password}
        )
        response_data = response.json()
        
        if response.status_code == 200:
            return templates.TemplateResponse("signup.html", {"request": request, "success": 'Вы успешно зарегистрировались'})
        else:
            return templates.TemplateResponse("signup.html", {"request": request, "error": response_data.get("detail", "Ошибка регистрации")})
    except Exception as e:
        return templates.TemplateResponse("signup.html", {"request": request, "error": f"Ошибка сервера: {str(e)}"})

@app.post("/login")
async def login_action(request: Request, email: str = Form(...), password: str = Form(...), client: httpx.AsyncClient = Depends(get_http_client)):
    """Send a login request to the auth service."""
    print("DEBUG: main_service in post login")
    try:
        response = await client.post(
            f"{AUTH_SERVICE_URL}/login",
            json={"email": email, "password": password}
        )
        response_data = response.json()
        
        if response.status_code == 200:
            token = response_data.get("token")
            response = RedirectResponse(url="/", status_code=303)
            response.set_cookie(
                key="access_token",
                value=token,
                httponly=True,
                secure=True,
                samesite="lax"
            )
            return response
        else:
            return templates.TemplateResponse("login.html", {"request": request, "error": response_data.get("detail", "Неверный email или пароль")})
    except Exception as e:
        return templates.TemplateResponse("login.html", {"request": request, "error": f"Ошибка сервера: {str(e)}"})

@app.get("/logout")
async def logout(response: Response):
    """Logout the user by clearing the access token cookie."""
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response
