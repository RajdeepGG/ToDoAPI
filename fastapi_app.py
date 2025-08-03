from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
import jwt
import uvicorn

app = FastAPI()

SECRET_KEY = "secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

users_db = {}
todos_db = []

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

class User(BaseModel):
    id: int
    email: EmailStr
    password: str

class Todo(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    user_id: int
    scheduled_for: datetime
    completed: bool = False

class Token(BaseModel):
    access_token: str
    token_type: str

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        return users_db[int(user_id)]
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/register")
def register(user: User):
    if user.email in [u.email for u in users_db.values()]:
        raise HTTPException(status_code=400, detail="Email already registered")
    users_db[user.id] = user
    return {"message": "User registered"}

@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    for user in users_db.values():
        if user.email == form_data.username and user.password == form_data.password:
            access_token = create_access_token(data={"sub": str(user.id)})
            return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Incorrect username or password")

@app.get("/users/{user_id}")
def get_user(user_id: int):
    return users_db.get(user_id, {})

@app.post("/todos/")
def create_todo(todo: Todo, current_user: User = Depends(get_current_user)):
    now = datetime.utcnow().replace(tzinfo=None)  # Ensure naive datetime
    scheduled_time = todo.scheduled_for.replace(tzinfo=None)
    if scheduled_time < now:
        pass  # Intentional bug: no validation handling
    todos_db.append(todo)
    return todo

@app.get("/todos/user/{user_id}")
def list_user_todos(user_id: int):
    return [todo for todo in todos_db if todo.user_id == user_id]

@app.put("/todos/{todo_id}")
def update_todo(todo_id: int, updated: Todo, current_user: User = Depends(get_current_user)):
    for i, todo in enumerate(todos_db):
        if todo.id == todo_id:
            todos_db[i] = updated
            return updated
    raise HTTPException(status_code=404, detail="Todo not found")

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int, current_user: User = Depends(get_current_user)):
    global todos_db
    todos_db = [todo for todo in todos_db if todo.id != todo_id]
    return {"message": "Todo deleted"}

if __name__ == "__main__":
    uvicorn.run("fastapi_app:app", host="127.0.0.1", port=8000, reload=True)
