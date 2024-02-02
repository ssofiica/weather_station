from rest_framework import permissions
from app.models import *
import redis
import json
from django.conf import settings

session_storage = redis.StrictRedis(host='127.0.0.1', port='6379')
key = "a4e0oinhl932as15"

class IsAsync(permissions.BasePermission):
    def has_permission(self, request, view):
        data = json.loads(request.body)
        input_key = data["key"]
        if (input_key==key):
            return True
        else: return False
        
class IsAuth(permissions.BasePermission):
    def has_permission(self, request, view):
        access_token = request.COOKIES.get("session_id", None)
        if (access_token): 
            return True
        else: return False

class IsAdmin(permissions.BasePermission): 
    def has_permission(self, request, view):
        print(request)
        access_token = request.COOKIES.get("session_id", None)
        print(access_token)
        if access_token is None: 
            print(access_token)
            return False 
        try: 
            username = session_storage.get(access_token).decode('utf-8') 
            print(username)
        except Exception as e: 
            return False 
        user = Users.objects.get(email=username)
        return user.is_superuser 
     
class IsCreator(permissions.BasePermission): 
    def has_permission(self, request, view): 
        access_token = request.COOKIES.get("session_id", None)
        print(access_token)
        if access_token is None: 
            return False 
        try: 
            username = session_storage.get(access_token).decode('utf-8') 
            print(username)
            print("ok")
        except Exception as e: 
            return False 
        user = Users.objects.get(email=username) 
        print("super : {}".format(user.is_superuser))
        if (user.is_superuser == False):
            print("true")
            return True
        else: return False