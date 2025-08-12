import os
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from authlib.integrations.starlette_client import OAuthError
from jose import JWTError, jwt
from dotenv import load_dotenv
import json

load_dotenv()

app = FastAPI(title="Wendler 5-3-1 API", version="0.1.0")

# Add session middleware for OAuth
app.add_middleware(SessionMiddleware, secret_key=os.getenv("JWT_SECRET", "your-secret-key"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# OAuth Configuration
oauth = OAuth()

# Google OAuth
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# GitHub OAuth
oauth.register(
    name='github',
    client_id=os.getenv('GITHUB_CLIENT_ID'),
    client_secret=os.getenv('GITHUB_CLIENT_SECRET'),
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'},
)

# Facebook OAuth
oauth.register(
    name='facebook',
    client_id=os.getenv('FACEBOOK_CLIENT_ID'),
    client_secret=os.getenv('FACEBOOK_CLIENT_SECRET'),
    access_token_url='https://graph.facebook.com/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    api_base_url='https://graph.facebook.com/',
    client_kwargs={'scope': 'email'},
)

JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
JWT_ALGORITHM = "HS256"

@app.get("/")
async def root():
    return {"message": "Wendler 5-3-1 API"}

@app.get("/auth/{provider}")
async def login(provider: str, request: Request):
    if provider not in ['google', 'github', 'facebook']:
        raise HTTPException(status_code=400, detail="Unsupported provider")
    
    client = oauth.create_client(provider)
    redirect_uri = request.url_for('callback', provider=provider)
    return await client.authorize_redirect(request, redirect_uri)

@app.get("/auth/{provider}/callback")
async def callback(provider: str, request: Request):
    if provider not in ['google', 'github', 'facebook']:
        raise HTTPException(status_code=400, detail="Unsupported provider")
    
    try:
        client = oauth.create_client(provider)
        token = await client.authorize_access_token(request)
        
        # Get user info based on provider
        if provider == 'google':
            user_info = token.get('userinfo')
            user_data = {
                "id": user_info['sub'],
                "email": user_info['email'],
                "name": user_info['name'],
                "provider": provider
            }
        elif provider == 'github':
            user_resp = await client.get('user', token=token)
            user_info = user_resp.json()
            user_data = {
                "id": str(user_info['id']),
                "email": user_info.get('email'),
                "name": user_info.get('name') or user_info['login'],
                "provider": provider
            }
        elif provider == 'facebook':
            user_resp = await client.get('me?fields=id,name,email', token=token)
            user_info = user_resp.json()
            user_data = {
                "id": user_info['id'],
                "email": user_info.get('email'),
                "name": user_info['name'],
                "provider": provider
            }
        
        # Create JWT token
        jwt_token = jwt.encode(user_data, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        # Return HTML that posts message to parent window and closes popup
        html_content = f"""
        <html>
        <body>
        <script>
            window.opener.postMessage({{
                access_token: '{jwt_token}',
                token_type: 'bearer',
                user: {json.dumps(user_data)}
            }}, 'http://localhost:3000');
            window.close();
        </script>
        <p>Login successful! This window should close automatically.</p>
        </body>
        </html>
        """
        return Response(content=html_content, media_type="text/html")
    
    except OAuthError as error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error.error}")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

@app.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, access_log=False)
