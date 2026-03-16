# FastAPI Best Practices: Input Validation and Authentication

**Date:** 2026-03-15
**Topic:** FastAPI best practices for input validation and authentication
**Sources:** FastAPI official docs, Pydantic v2 docs, OWASP cheat sheets, TestDriven.io, fastapi-jwt-auth docs, Authlib docs

---

## Executive Summary

FastAPI's type-annotation-driven design makes input validation and authentication declarative and composable. The key tools are:

- **Pydantic v2** for request body validation with `Field()`, `@field_validator`, and `@model_validator`
- **`Annotated` + `Query()`/`Path()`** for parameter-level constraints
- **`Depends()` / `Security()`** for auth dependency injection
- **OAuth2PasswordBearer + JWT** (PyJWT + pwdlib[argon2]) for stateless bearer auth
- **OAuth2 Scopes** for standards-compliant RBAC

The core recommendation: validate at every boundary (request body, query params, path params, file uploads), forbid extra fields on security-sensitive models, and chain auth logic via FastAPI's dependency injection rather than inline checks.

---

## Part 1: Input Validation

### 1.1 Pydantic v2 Models for Request Body Validation

FastAPI reads the request body as JSON, converts types, validates data, and returns structured HTTP 422 errors automatically — all from a single type annotation.

#### Basic Model with `Field()` Constraints

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field, ConfigDict

app = FastAPI()

class Item(BaseModel):
    model_config = ConfigDict(extra='forbid')  # reject unexpected keys

    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(
        default=None,
        title="The description of the item",
        max_length=300
    )
    price: float = Field(gt=0, description="Must be greater than zero")
    tax: float | None = None
```

**Full `Field()` constraint reference:**

| Constraint | Types | Description |
|---|---|---|
| `gt` / `ge` / `lt` / `le` | numeric | Greater/less than (exclusive/inclusive) |
| `multiple_of` | numeric | Value must be a multiple of N |
| `max_digits` / `decimal_places` | Decimal | Precision constraints |
| `min_length` / `max_length` | string | Character count bounds |
| `pattern` | string | Regex pattern (Pydantic v2; replaces `regex`) |

#### Forbidding Extra Fields

Security-sensitive models should reject unexpected keys, preventing mass-assignment vulnerabilities:

```python
from pydantic import BaseModel, ConfigDict

class StrictUser(BaseModel):
    model_config = ConfigDict(extra='forbid')
    username: str
    email: str
```

Sending `{"username": "alice", "email": "a@b.com", "admin": true}` returns:
```json
{"type": "extra_forbidden", "loc": ["body", "admin"], "msg": "Extra inputs are not permitted"}
```

#### `@field_validator` (Single-field Validation)

```python
from pydantic import BaseModel, field_validator

class UserCreate(BaseModel):
    username: str
    email: str
    age: int

    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v.lower()

    @field_validator('age')
    @classmethod
    def age_must_be_adult(cls, v: int) -> int:
        if v < 18:
            raise ValueError('Must be 18 or older')
        return v

    @field_validator('email', mode='before')
    @classmethod
    def strip_email(cls, v) -> str:
        # mode='before': v is raw input before Pydantic parses it
        if isinstance(v, str):
            return v.strip().lower()
        return v
```

**Validator modes:**
- `mode='after'` (default): receives already-typed/coerced value — safest
- `mode='before'`: receives raw input before parsing

#### `@model_validator` (Cross-field Validation)

```python
from pydantic import BaseModel, model_validator
from typing import Self

class DateRange(BaseModel):
    start_date: datetime
    end_date: datetime
    password: str
    confirm_password: str

    @model_validator(mode='after')
    def check_constraints(self) -> Self:
        if self.end_date <= self.start_date:
            raise ValueError('end_date must be after start_date')
        if self.password != self.confirm_password:
            raise ValueError('Passwords do not match')
        return self
```

#### Reusable Annotated Validators

Define reusable type aliases using `AfterValidator`, `BeforeValidator`, etc.:

```python
from typing import Annotated
from pydantic import AfterValidator, BaseModel

def is_positive(v: float) -> float:
    if v <= 0:
        raise ValueError('Must be positive')
    return v

PositiveFloat = Annotated[float, AfterValidator(is_positive)]

class Order(BaseModel):
    total: PositiveFloat
```

---

### 1.2 Path and Query Parameter Validation

The `Annotated` syntax is the **modern, recommended approach**. It separates the type from validation metadata and is testable outside FastAPI.

#### `Query()` Constraints

```python
from typing import Annotated
from fastapi import FastAPI, Query

@app.get("/search/")
async def search(
    q: Annotated[str | None, Query(
        min_length=3,
        max_length=100,
        pattern=r"^[\w\s\-]+$",
        alias="search-query",
    )] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    ...
```

**Full `Query()` parameter reference:**

| Parameter | Purpose |
|---|---|
| `min_length` / `max_length` | String length bounds |
| `pattern` | Regex pattern |
| `ge` / `gt` / `le` / `lt` | Numeric bounds |
| `alias` | Alternative URL param name (e.g. `search-query`) |
| `deprecated=True` | Mark deprecated in OpenAPI docs |
| `include_in_schema=False` | Hide from OpenAPI schema |

**Multi-value query parameters:**
```python
@app.get("/items/")
async def get_items(
    tags: Annotated[list[str] | None, Query()] = None
    # URL: /items/?tags=foo&tags=bar  →  tags = ["foo", "bar"]
):
    ...
```

#### `Path()` Constraints

Path parameters are always required; numeric and string constraints work identically to `Query()`:

```python
from fastapi import Path

@app.get("/items/{item_id}")
async def read_item(
    item_id: Annotated[int, Path(
        title="Item primary key",
        gt=0,
        le=999_999,
    )],
):
    ...
```

---

### 1.3 Custom Error Handling

#### `HTTPException` for Application-Level Errors

```python
from fastapi import HTTPException

@app.get("/items/{item_id}")
async def read_item(item_id: str):
    if item_id not in db:
        raise HTTPException(
            status_code=404,
            detail={"error": "Item not found", "item_id": item_id},
            headers={"X-Error": "not-found"},
        )
    return db[item_id]
```

#### Overriding `RequestValidationError` (Custom 422 Format)

```python
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        errors.append({
            "field": " -> ".join(str(loc) for loc in err["loc"]),
            "message": err["msg"],
            "type": err["type"],
        })
    return JSONResponse(
        status_code=422,
        content={"status": "validation_error", "errors": errors},
    )
```

Each error in `exc.errors()` contains `loc` (field path), `msg` (human-readable), and `type` (Pydantic error code).

#### Custom Domain Exceptions

```python
class ItemNotFoundError(Exception):
    def __init__(self, item_id: int):
        self.item_id = item_id

@app.exception_handler(ItemNotFoundError)
async def item_not_found_handler(request: Request, exc: ItemNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"error": "item_not_found", "item_id": exc.item_id},
    )
```

---

### 1.4 Nested Models and Complex Data Structures

```python
from pydantic import BaseModel, HttpUrl

class Image(BaseModel):
    url: HttpUrl        # validates http/https URLs
    name: str
    width: int = Field(gt=0)
    height: int = Field(gt=0)

class Item(BaseModel):
    name: str
    price: float
    tags: set[str] = set()          # duplicates auto-deduplicated
    image: Image | None = None      # optional nested model
    attributes: dict[str, str] = {} # typed dictionary
```

**Built-in semantic types (Pydantic v2):**

| Type | Validates | Notes |
|---|---|---|
| `HttpUrl` | http/https URLs | Max 2083 chars |
| `EmailStr` | RFC 5321 email | Requires `email-validator` package |
| `IPvAnyAddress` | IPv4 or IPv6 | — |
| `UUID` | UUID strings → `uuid.UUID` | stdlib |
| `datetime` / `date` | ISO 8601 strings | stdlib |

---

### 1.5 File Upload Validation

```bash
pip install python-multipart python-magic
```

```python
from fastapi import UploadFile, File, HTTPException
from typing import Annotated
import magic
import uuid
import os

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

@app.post("/upload/secure/")
async def secure_upload(
    file: Annotated[UploadFile, File(description="Image file (JPEG/PNG/WebP)")]
):
    # 1. Validate extension
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="File extension not allowed")

    contents = await file.read()

    # 2. Validate file size
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 5 MB)")

    # 3. Verify actual content (not just declared content_type)
    detected_type = magic.from_buffer(contents, mime=True)
    if detected_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="File content does not match allowed types")

    # 4. Store with safe server-generated filename (never use file.filename as path)
    safe_filename = f"{uuid.uuid4()}{ext}"
    return {"stored_as": safe_filename}
```

**OWASP file upload security principles:**
- Use an **allowlist of extensions** — never a denylist
- **Rename files server-side** with a random identifier (never use `file.filename` as a storage path)
- **Verify actual content** via magic bytes, not just the declared `content_type` (clients can lie)
- Store uploads **outside the web root**
- Enforce **size limits before** processing content

---

### 1.6 Real-World Example: User Registration

```python
from fastapi import FastAPI
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator, ConfigDict
from typing import Annotated, Self

class UserCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    username: str = Field(
        min_length=3, max_length=30,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="Alphanumeric + underscore only"
    )
    email: EmailStr
    age: int = Field(ge=18, le=120)
    password: str = Field(min_length=8)
    confirm_password: str

    @field_validator('username')
    @classmethod
    def username_not_reserved(cls, v: str) -> str:
        reserved = {'admin', 'root', 'system'}
        if v.lower() in reserved:
            raise ValueError(f'"{v}" is a reserved username')
        return v

    @model_validator(mode='after')
    def passwords_match(self) -> Self:
        if self.password != self.confirm_password:
            raise ValueError('Passwords do not match')
        return self

@app.post("/users/", status_code=201)
async def register_user(user: UserCreate):
    user_data = user.model_dump(exclude={'confirm_password'})
    # hash password, save to DB ...
    return {"username": user_data["username"], "email": user_data["email"]}
```

---

## Part 2: Authentication and Authorization

### 2.1 OAuth2 with Password Flow and JWT Tokens

#### Installation (Recommended Stack, 2026)

```bash
pip install pyjwt "pwdlib[argon2]"
```

> "If you use python-jose, you need to install some extra dependencies." — FastAPI docs (recommending PyJWT instead)

The older `python-jose` + `passlib[bcrypt]` stack is less preferred as of FastAPI's current docs.

#### Configuration

```python
from datetime import datetime, timedelta, timezone
import jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pwdlib import PasswordHash

SECRET_KEY = "generated-with-openssl-rand-hex-32"  # minimum 64 chars in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

password_hash = PasswordHash.recommended()  # uses Argon2id
DUMMY_HASH = password_hash.hash("dummypassword")  # for timing attack prevention
```

**OWASP requirement**: HMAC secrets must be **at least 64 characters** from a CSPRNG. Generate with: `openssl rand -hex 32`

#### Password Hashing and Verification

```python
def verify_password(plain: str, hashed: str) -> bool:
    return password_hash.verify(plain, hashed)

def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        verify_password(password, DUMMY_HASH)  # timing attack prevention
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user
```

> "Even when user doesn't exist, `verify_password` is called against `DUMMY_HASH` to prevent timing attacks that could enumerate valid usernames." — FastAPI docs

#### Token Creation and Login Endpoint

```python
from pydantic import BaseModel
from fastapi import status

class Token(BaseModel):
    access_token: str
    token_type: str

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": f"username:{user.username}"},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=access_token, token_type="bearer")
```

**Note on the `sub` claim**: Best practice is to prefix it to avoid collisions: `"sub": f"username:{user.username}"`.

**Algorithm security (OWASP)**: Always pass `algorithms=[ALGORITHM]` to `jwt.decode()`. This prevents the `alg: none` attack where an attacker strips the signature by declaring no algorithm.

---

### 2.2 API Key Authentication

FastAPI provides `APIKeyHeader`, `APIKeyQuery`, and `APIKeyCookie` in `fastapi.security`.

#### Header-Based API Key (Preferred)

```python
from fastapi.security import APIKeyHeader
from fastapi import Security, HTTPException, status

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != VALID_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key",
        )
    return api_key

@app.get("/protected/")
async def protected_route(api_key: str = Security(get_api_key)):
    return {"message": "Access granted"}
```

**OWASP guidance**: API keys in query params appear in server logs and browser history — prefer header-based keys. Return `429 Too Many Requests` for rate limit violations.

#### Supporting Multiple Auth Methods

```python
async def get_auth(
    jwt_token: str = Security(oauth2_scheme),
    api_key: str = Security(api_key_header),
):
    if api_key:
        return validate_api_key(api_key)
    if jwt_token:
        return validate_jwt(jwt_token)
    raise HTTPException(status_code=401, detail="Not authenticated")
```

Set `auto_error=False` on each scheme to combine them gracefully.

---

### 2.3 HTTP Basic Auth

Appropriate for simple internal APIs and machine-to-machine communication. **Must run over HTTPS.**

```python
import secrets
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

def get_current_username(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> str:
    is_correct_username = secrets.compare_digest(
        credentials.username.encode("utf8"), b"admin"
    )
    is_correct_password = secrets.compare_digest(
        credentials.password.encode("utf8"), b"supersecret"
    )
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
```

**Why `secrets.compare_digest()`**: Standard `==` short-circuits on the first differing character, leaking timing information.

> "Simple string comparison (`==`) fails fast on mismatch... Attackers can measure response times to guess credentials character-by-character." — FastAPI docs

**Limitation**: HTTP Basic Auth has no built-in logout or token expiration. Prefer JWT/OAuth2 for user-facing applications.

---

### 2.4 Dependency Injection for Auth (`Depends()`)

FastAPI's dependency injection is the cornerstone of its security model. Auth logic is defined once and reused across endpoints.

#### Dependency Chain Pattern

```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Layer 1: Extract and validate JWT
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception
    user = get_user(db, username=username)
    if user is None:
        raise credentials_exception
    return user

# Layer 2: Enforce business rules
async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.get("/users/me/")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    return current_user
```

#### Scope: Endpoint, Router, or App-Wide

```python
# Per-endpoint
@app.get("/items/", dependencies=[Depends(verify_token)])

# Per-router (all routes in the router)
router = APIRouter(dependencies=[Depends(verify_token)])

# App-wide (all routes)
app = FastAPI(dependencies=[Depends(verify_api_key)])
```

---

### 2.5 Role-Based Access Control (RBAC)

#### Approach A: OAuth2 Scopes (Recommended)

Standards-based approach used by Google, GitHub, Facebook, and Microsoft.

```python
from fastapi import Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "users:read": "Read user information.",
        "users:write": "Create and modify users.",
        "admin": "Full administrative access.",
    },
)

async def get_current_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    authenticate_value = (
        f'Bearer scope="{security_scopes.scope_str}"'
        if security_scopes.scopes else "Bearer"
    )
    # ... decode JWT and extract token_data.scopes ...

    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    return user

# Declare required scopes with Security()
@app.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[User, Security(get_current_active_user, scopes=["items:read"])],
):
    ...
```

> "Scopes propagate through the dependency tree." — FastAPI docs

> "Only assign scopes that users are actually authorized to have. Don't blindly trust requested scopes." — OWASP

#### Approach B: Role Claims in JWT (Simpler)

```python
def require_role(required_role: str):
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if required_role not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required",
            )
        return current_user
    return role_checker

@app.delete("/admin/users/{user_id}")
async def admin_delete_user(
    user: Annotated[User, Depends(require_role("admin"))],
):
    ...
```

---

### 2.6 Security Headers and CORS

#### CORS (CORSMiddleware)

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)
```

**Critical rule**: When `allow_credentials=True`, you **cannot** use `"*"` wildcards for origins, methods, or headers — all must be explicitly specified (browser hard requirement per MDN/RFC).

> "Using `'*'` as wildcard allows all origins BUT excludes credential-based communication (Cookies, Authorization headers, Bearer tokens)." — FastAPI docs

#### Built-in Security Middleware

```python
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(HTTPSRedirectMiddleware)  # Redirect HTTP → HTTPS
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["example.com", "*.example.com"],  # Block Host header injection
)
```

#### Custom Security Headers Middleware

```python
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "frame-ancestors 'none'"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

**OWASP-required headers:**

| Header | Value | Purpose |
|---|---|---|
| `Cache-Control` | `no-store` | Prevent sensitive data caching |
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Enforce HTTPS |
| `Content-Security-Policy` | `frame-ancestors 'none'` | Prevent clickjacking |
| `X-Frame-Options` | `DENY` | Legacy clickjacking protection |

---

### 2.7 Refresh Tokens and Token Revocation

The FastAPI docs do not cover refresh tokens — these patterns come from the `fastapi-jwt-auth` library and OWASP JWT Cheat Sheet.

#### Refresh Token Pattern

```python
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30

def create_tokens(user_id: str) -> dict:
    access_token = create_access_token(
        data={"sub": user_id, "type": "access"},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_access_token(
        data={"sub": user_id, "type": "refresh"},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@app.post("/auth/refresh")
async def refresh_access_token(
    refresh_token: Annotated[str, Depends(oauth2_scheme)],
) -> Token:
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    new_access_token = create_access_token(
        data={"sub": payload.get("sub"), "type": "access"},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=new_access_token, token_type="bearer")
```

> "Refresh tokens cannot access an endpoint protected with jwt_required() and vice versa." — fastapi-jwt-auth docs

#### Token Revocation via Redis Denylist

```python
import redis
import uuid

r = redis.Redis(host="localhost", port=6379, db=0)

# Include jti claim at creation time
to_encode.update({"jti": str(uuid.uuid4())})

@app.post("/auth/logout")
async def logout(token: Annotated[str, Depends(oauth2_scheme)]):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    jti = payload.get("jti")
    exp = payload.get("exp")
    ttl = exp - int(datetime.now(timezone.utc).timestamp())
    r.setex(f"revoked:{jti}", ttl, "1")  # auto-deleted by Redis after natural expiry
    return {"message": "Logged out successfully"}
```

> "Memory stores are great for revoking tokens on logout. After the TTL, tokens are automatically deleted." — fastapi-jwt-auth docs

> "Implement a denylist storing SHA-256 token digests with revocation dates." — OWASP JWT Cheat Sheet

---

### 2.8 Session-Based Auth vs. Stateless JWT

| Aspect | Session-Based | Stateless JWT |
|---|---|---|
| State storage | Server (DB/Redis) | Client (token payload) |
| Revocation | Immediate (delete row) | Requires denylist or short expiry |
| Scalability | Requires shared session store | Scales horizontally without shared state |
| CSRF risk | High (cookies auto-sent) | Low (Bearer header, not auto-sent) |
| XSS risk | Lower (HttpOnly cookie) | Higher (if stored in localStorage) |
| Logout | Immediate and complete | Delayed until token expiry |
| DB lookup per request | Yes | No (verify signature only) |

**OWASP JWT storage guidance:**
> "Store tokens in browser `sessionStorage` and add them as Bearer headers in API requests. Avoid cookies (auto-sent) and localStorage (persists after restart)." — OWASP JWT Cheat Sheet

**Cookie security requirements (OWASP)** when using sessions:

| Attribute | Value | Purpose |
|---|---|---|
| `Secure` | Always | HTTPS only |
| `HttpOnly` | Always | Block JavaScript access |
| `SameSite` | `Strict` or `Lax` | CSRF mitigation |

---

### 2.9 Third-Party OAuth (Google, GitHub) with Authlib

```bash
pip install authlib httpx
```

```python
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware

app.add_middleware(SessionMiddleware, secret_key="your-session-secret-key")

oauth = OAuth()
oauth.register(
    name="google",
    client_id="your-google-client-id",
    client_secret="your-google-client-secret",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

@app.get("/login/google")
async def login_via_google(request: Request):
    redirect_uri = request.url_for("auth_via_google")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth/google")
async def auth_via_google(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")
    # Exchange provider user for your own JWT
    db_user = await upsert_user_from_google(user_info)
    app_jwt = create_access_token(
        data={"sub": str(db_user.id), "roles": db_user.roles},
        expires_delta=timedelta(minutes=30),
    )
    return {"access_token": app_jwt, "token_type": "bearer"}
```

**Recommended pattern (from FastAPI maintainer)**: Issue your own app-specific JWT (not the provider's token). This keeps your application auth independent of provider tokens and lets you add app-specific roles/scopes.

---

## Recommendations

### Input Validation

1. **Always use `Annotated` syntax** with `Query()`, `Path()`, and `Field()` — it's the modern recommended form and testable outside FastAPI.
2. **Set `model_config = ConfigDict(extra='forbid')`** on all security-sensitive request models to prevent mass-assignment attacks.
3. **Use `@model_validator(mode='after')`** for cross-field constraints (password confirmation, date ranges).
4. **Define reusable `Annotated` type aliases** (e.g., `PositiveFloat`) for constraints used across multiple models.
5. **Override `RequestValidationError`** to standardize the 422 error response shape for API consumers.
6. **File uploads**: validate extension (allowlist) + verify magic bytes + rename server-side + enforce size limits before processing.

### Authentication

1. **Use PyJWT + pwdlib[argon2]** — the current FastAPI recommendation over python-jose + passlib.
2. **Always pass `algorithms=[ALGORITHM]`** to `jwt.decode()` to prevent the `alg: none` attack.
3. **Use `secrets.compare_digest()`** for all credential comparisons (timing-safe).
4. **Always call dummy hash verify** for non-existent users to prevent username enumeration via timing.
5. **Use OAuth2 Scopes** with `Security()` for standards-compliant RBAC rather than ad-hoc role checks.
6. **For revocable tokens**: add `jti` claim + Redis denylist on logout with natural TTL expiry.
7. **Never use `"*"` CORS wildcards** when `allow_credentials=True` — enumerate origins, methods, and headers explicitly.
8. **Add security headers middleware** (HSTS, X-Frame-Options, CSP, Cache-Control) — FastAPI has no built-in security headers.
9. **For third-party OAuth**: exchange the provider token for your own app JWT before returning to the client.

---

## Sources

### Input Validation
1. FastAPI docs — Request Body: https://fastapi.tiangolo.com/tutorial/body/
2. FastAPI docs — Query Params & String Validation: https://fastapi.tiangolo.com/tutorial/query-params-str-validations/
3. FastAPI docs — Path Params & Numeric Validation: https://fastapi.tiangolo.com/tutorial/path-params-numeric-validations/
4. FastAPI docs — Body Fields: https://fastapi.tiangolo.com/tutorial/body-fields/
5. FastAPI docs — Nested Models: https://fastapi.tiangolo.com/tutorial/body-nested-models/
6. FastAPI docs — Request Files: https://fastapi.tiangolo.com/tutorial/request-files/
7. FastAPI docs — Handling Errors: https://fastapi.tiangolo.com/tutorial/handling-errors/
8. Pydantic v2 docs — Validators: https://docs.pydantic.dev/latest/concepts/validators/
9. Pydantic v2 docs — Fields: https://docs.pydantic.dev/latest/concepts/fields/
10. OWASP Input Validation Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html

### Authentication
11. FastAPI docs — Security: https://fastapi.tiangolo.com/tutorial/security/
12. FastAPI docs — OAuth2 with Password Flow: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
13. FastAPI docs — OAuth2 Scopes: https://fastapi.tiangolo.com/advanced/security/oauth2-scopes/
14. FastAPI docs — HTTP Basic Auth: https://fastapi.tiangolo.com/advanced/security/http-basic-auth/
15. FastAPI docs — CORS: https://fastapi.tiangolo.com/tutorial/cors/
16. FastAPI docs — Middleware: https://fastapi.tiangolo.com/advanced/middleware/
17. Starlette Authentication docs: https://www.starlette.io/authentication/
18. OWASP REST Security Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html
19. OWASP JWT Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Tokens_Cheat_Sheet_for_Java.html
20. OWASP Authentication Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
21. OWASP Session Management Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
22. fastapi-jwt-auth docs: https://indominusbyte.github.io/fastapi-jwt-auth/
23. Authlib docs — Starlette/FastAPI integration: https://docs.authlib.org/en/latest/client/starlette.html
