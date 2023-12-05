from rest_framework import permissions
from app.models import *
import redis
from django.conf import settings

session_storage = redis.StrictRedis(host='127.0.0.1', port='6379')

class IsAdmin(permissions.BasePermission): 
    def has_permission(self, request, view):
        access_token = request.COOKIES["session_id"]
        if access_token is None: 
            return False 
        try: 
            username = session_storage.get(access_token).decode('utf-8') 
        except Exception as e: 
            return False 
        user = Users.objects.get(email=username)
        return user.is_superuser 
     
class IsCreator(permissions.BasePermission): 
    def has_permission(self, request, view): 
        access_token = request.COOKIES["session_id"]
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
        if (user.is_staff == True and user.is_superuser == False):
            print("true")
            return True
        else: return False