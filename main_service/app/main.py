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

@app.get("/signup/seller", response_class=HTMLResponse)
async def signup_seller(request: Request):
    return templates.TemplateResponse("signup_seller.html", {"request": request})

@app.post("/register/seller")
async def register_seller(request: Request, email: str = Form(...), password: str = Form(...), shop_name: str = Form(...), inn: str = Form(None), description: str = Form(None), client: httpx.AsyncClient = Depends(get_http_client)):
    """Отправить запрос на регистрацию продавца в auth_service."""
    try:
        response = await client.post(
            f"{AUTH_SERVICE_URL}/register/seller",
            json={
                "email": email,
                "password": password,
                "shop_name": shop_name,
                "inn": inn,
                "description": description
            }
        )
        response_data = response.json()
        if response.status_code == 200:
            return templates.TemplateResponse("signup_seller.html", {"request": request, "success": 'Вы успешно зарегистрировались как продавец!'})
        else:
            return templates.TemplateResponse("signup_seller.html", {"request": request, "error": response_data.get("detail", "Ошибка регистрации продавца")})
    except Exception as e:
        return templates.TemplateResponse("signup_seller.html", {"request": request, "error": f"Ошибка сервера: {str(e)}"})

@app.get("/seller/add_product", response_class=HTMLResponse)
async def seller_add_product_page(request: Request, client: httpx.AsyncClient = Depends(get_http_client)):
    jwt_token = request.cookies.get("access_token")
    if not jwt_token:
        return RedirectResponse(url="/login", status_code=303)
    try:
        payload = jwt.decode(jwt_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
    except Exception:
        return RedirectResponse(url="/login", status_code=303)
    # Проверяем роль через auth_service
    role_resp = await client.get(f"{AUTH_SERVICE_URL}/role?email={email}")
    role = role_resp.json().get("role")
    if role != "seller":
        return RedirectResponse(url="/profile", status_code=303)
    return templates.TemplateResponse("seller_add_product.html", {"request": request})

@app.post("/seller/add_product")
async def seller_add_product(request: Request, client: httpx.AsyncClient = Depends(get_http_client)):
    form = await request.form()
    # Определяем, что отправлено: один товар или файл
    if "file" in form and form["file"]:
        # Загрузка файла с несколькими товарами
        upload_file = form["file"]
        files = {"file": (upload_file.filename, await upload_file.read(), upload_file.content_type)}
        response = await client.post(f"{CATALOG_SERVICE_URL}/api/products/bulk_upload", files=files)
        result = await response.aread()
        return templates.TemplateResponse("seller_add_product.html", {"request": request, "result": result.decode()})
    else:
        # Добавление одного товара
        name = form.get("name")
        price = form.get("price")
        category = form.get("category")
        description = form.get("description")
        # Получаем seller_id из куки или профиля (тут пример — доработать под свою авторизацию)
        jwt_token = request.cookies.get("access_token")
        if not jwt_token:
            return templates.TemplateResponse("seller_add_product.html", {"request": request, "error": "Необходима авторизация"})
        # Получаем email из токена
        try:
            payload = jwt.decode(jwt_token, SECRET_KEY, algorithms=[ALGORITHM])
            email = payload.get("sub")
        except Exception:
            return templates.TemplateResponse("seller_add_product.html", {"request": request, "error": "Ошибка авторизации"})
        # Получаем seller_id через auth_service
        seller_resp = await client.get(f"{AUTH_SERVICE_URL}/get_user_id?email={email}")
        seller_id = seller_resp.json().get("user_id")
        product_data = {
            "name": name,
            "price": price,
            "description": description,
            "seller_id": seller_id,
            "stock": 1,           # по умолчанию 1
            "active": True,       # по умолчанию True
            "category_id": 1      # временно, если нет выбора категории
        }
        response = await client.post(f"{CATALOG_SERVICE_URL}/products", json=product_data)
        result = response.json()
        if response.status_code == 200:
            return templates.TemplateResponse("seller_add_product.html", {"request": request, "success": "Товар успешно добавлен!"})
        else:
            return templates.TemplateResponse("seller_add_product.html", {"request": request, "error": result.get("detail", "Ошибка добавления товара")})

@app.get("/seller/edit_product", response_class=HTMLResponse)
async def seller_edit_product_page(request: Request, id: int, client: httpx.AsyncClient = Depends(get_http_client)):
    jwt_token = request.cookies.get("access_token")
    if not jwt_token:
        return RedirectResponse(url="/login", status_code=303)
    try:
        payload = jwt.decode(jwt_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        user_id = payload.get("id") # Получаем user_id из токена
    except Exception:
        return RedirectResponse(url="/login", status_code=303)

    # Проверяем роль через auth_service
    role_resp = await client.get(f"{AUTH_SERVICE_URL}/role?email={email}")
    role = role_resp.json().get("role")
    if role != "seller":
        return RedirectResponse(url="/profile", status_code=303)

    # Получаем информацию о товаре
    product_resp = await client.get(f"{CATALOG_SERVICE_URL}/api/get_product?id={id}")
    if not product_resp.status_code == 200:
        raise HTTPException(status_code=product_resp.status_code, detail="Товар не найден или ошибка загрузки")
    product = product_resp.json()

    # Проверяем, что товар принадлежит текущему продавцу
    if product.get("seller_id") != user_id:
        return RedirectResponse(url="/profile", status_code=303) # Или другая страница ошибки/перенаправления

    return templates.TemplateResponse("seller_edit_product.html", {"request": request, "product": product})

@app.post("/seller/update_product")
async def seller_update_product(request: Request, id: int = Form(...), name: str = Form(...), price: float = Form(...), description: str = Form(None), client: httpx.AsyncClient = Depends(get_http_client)):
    jwt_token = request.cookies.get("access_token")
    if not jwt_token:
        raise HTTPException(status_code=401, detail="Необходима авторизация")
    try:
        payload = jwt.decode(jwt_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
    except Exception:
        raise HTTPException(status_code=401, detail="Ошибка авторизации")

    # Получаем информацию о товаре, чтобы проверить владельца
    product_resp = await client.get(f"{CATALOG_SERVICE_URL}/api/get_product?id={id}")
    if not product_resp.status_code == 200:
        raise HTTPException(status_code=product_resp.status_code, detail="Товар не найден")
    product_data_from_db = product_resp.json()

    if product_data_from_db.get("seller_id") != user_id:
        raise HTTPException(status_code=403, detail="У вас нет прав на изменение этого товара")

    update_data = {
        "id": id,
        "name": name,
        "price": price,
        "description": description,
        "stock": product_data_from_db.get("stock", 0), # Используем существующее значение или дефолтное
        "active": product_data_from_db.get("active", True), # Используем существующее значение или дефолтное
        "category_id": product_data_from_db.get("category_id", 1), # Используем существующее значение или дефолтное
        "seller_id": product_data_from_db.get("seller_id"), # Используем существующее значение
    }

    response = await client.put(f"{CATALOG_SERVICE_URL}/edit_product/{id}", json=update_data, headers={"Authorization": f"Bearer {jwt_token}"})
    result = response.json()

    if response.status_code == 200:
        return RedirectResponse(url=f"/product?id={id}", status_code=303)
    else:
        raise HTTPException(status_code=response.status_code, detail=result.get("detail", "Ошибка при обновлении товара"))

@app.get("/seller/metrics", response_class=HTMLResponse)
async def seller_metrics_page(request: Request, client: httpx.AsyncClient = Depends(get_http_client)):
    jwt_token = request.cookies.get("access_token")
    if not jwt_token:
        return RedirectResponse(url="/login", status_code=303)
    try:
        payload = jwt.decode(jwt_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
    except Exception:
        return RedirectResponse(url="/login", status_code=303)

    # Проверяем роль через auth_service
    role_resp = await client.get(f"{AUTH_SERVICE_URL}/role?email={email}")
    role = role_resp.json().get("role")
    if role != "seller":
        return RedirectResponse(url="/profile", status_code=303)
    
    return templates.TemplateResponse("seller_metrics.html", {"request": request})

@app.post("/seller/delete_product")
async def seller_delete_product(request: Request, id: int = Form(...), client: httpx.AsyncClient = Depends(get_http_client)):
    jwt_token = request.cookies.get("access_token")
    if not jwt_token:
        raise HTTPException(status_code=401, detail="Необходима авторизация")
    try:
        payload = jwt.decode(jwt_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
    except Exception:
        raise HTTPException(status_code=401, detail="Ошибка авторизации")

    # Получаем информацию о товаре, чтобы проверить владельца
    product_resp = await client.get(f"{CATALOG_SERVICE_URL}/api/get_product?id={id}")
    if not product_resp.status_code == 200:
        raise HTTPException(status_code=product_resp.status_code, detail="Товар не найден")
    product_data_from_db = product_resp.json()

    if product_data_from_db.get("seller_id") != user_id:
        raise HTTPException(status_code=403, detail="У вас нет прав на удаление этого товара")

    response = await client.delete(f"{CATALOG_SERVICE_URL}/products/{id}", headers={"Authorization": f"Bearer {jwt_token}"})

    if response.status_code == 200:
        return RedirectResponse(url="/", status_code=303) # После удаления перенаправляем на профиль
    else:
        raise HTTPException(status_code=response.status_code, detail="Ошибка при удалении товара")
