""" carry functions that makes code look bulky"""
from fastapi import Request, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from config import get_settings
from datetime import timedelta, datetime
from database import model, script
from passlib.context import CryptContext
from sqlalchemy import or_
from sqlalchemy.orm import Session

bcrpyt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")


def generate_jwt(username, role, expires_delta):
    encode = {'sub': username, 'role': role}
    expires = datetime.utcnow() + expires_delta
    encode.update({'exp': expires})
    jwt_token = jwt.encode(encode, get_settings().SECRET_KEY, algorithm=get_settings().ALGORITHM)
    return jwt_token

#checks availability of user's username and password
def authenticate_user(username:str, password: str, role: str, expires_delta: timedelta, db:script.db_session):
        
    scan_users = db.query(model.User).all()
    scan_org = db.query(model.Organization).all()

    if role == 'administrator':
        for row in scan_org:
            if row.email == username and bcrpyt_context.verify(password, row.password):
                return generate_jwt(username, role, expires_delta)
    else:
        for row in scan_users:
            if row.email == username and bcrpyt_context.verify(password, row.password):
                return generate_jwt(username, role, expires_delta)
            
    return False  # Authentication failed
            
            
def get_staff_from_token(request: Request, db: Session):
    """
    Decode the JWT token, extract username/email, 
    then authenticate if the user exists in the database.
    Returns the user if authenticated, else raises 401 Unauthorized.
    """
    try:
        token = request.cookies.get("access_token")
        if not token:
            return None 
        # Decode the token
        payload = jwt.decode(token, get_settings().SECRET_KEY, algorithms=[get_settings().ALGORITHM])
        username: str = payload.get("sub")
        
        if not username:
            return None
        
        # Query the user
        user = db.query(model.User).filter(model.User.email == username).first()
        if user:
            return user
        return None
    
    except JWTError:  # Catches token-related errors
        raise HTTPException(status_code=401, detail="Token expired or invalid")
    except Exception as e:  # General exception handling
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


def get_user_from_token(request: Request, db: Session):
    """
    Decode the JWT token, extract username/email, 
    then authenticate if the user exists in the database.
    Returns the user and role if authenticated, else raises 401 Unauthorized.
    """
    try:
        token = request.cookies.get("access_token")
        if not token:
            return None
        # Decode the token
        payload = jwt.decode(token, get_settings().SECRET_KEY, algorithms=[get_settings().ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        
        if not username or not role:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Query the user
        user = db.query(model.Organization).filter(model.Organization.email == username).first()

        if user:
            return {"user": user, "role": role}
        return None
    
    except JWTError:  # Catches token-related errors
        raise HTTPException(status_code=401, detail="Token expired or invalid")



