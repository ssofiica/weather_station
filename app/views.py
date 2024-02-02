from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from app.serializers import PhenomensSerializer, PhenomRecordSerializer, RequestSerializer, UserSerializer, DraftSerializer, UserLoginSerializer
from app.models import Phenomens, PhenomRecord, Request, Users
from datetime import date
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import authentication_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny
from rest_framework.decorators import permission_classes
from app.permissions import IsAdmin, IsCreator, IsAuth, IsAsync
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from django.conf import settings
import redis
import json
import requests
import uuid
from django.contrib.sessions.models import Session
from minio import Minio
import io

session_storage = redis.StrictRedis(host='127.0.0.1', port='6379')
go_url = 'http://localhost:8080/set_temperature'
key = "a4e0oinhl932as15"

client = Minio(endpoint="localhost:9000",   # адрес сервера
               access_key='minio',          # логин админа
               secret_key='minio124',       # пароль админа
               secure=False) 

class PhenomensList(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    model_class = Phenomens
    serializer_class = PhenomensSerializer
    
    def get(self, request, format=None):
        """
        Возвращает список природных явлений
        """
        phenomens = self.model_class.objects.all()
        data = []
        input_phenom = request.GET.get('value')#value - название явления
        if (input_phenom):
            phenom = self.model_class.objects.exclude(status='Удален').get(phenom_name=input_phenom)
            data.append(phenom)
        else:
        #если поле пусто, просто сохраняем все явления
            phenoms = self.model_class.objects.exclude(status='Удален')
            data = [i for i in phenoms]
            input_phenom = ''
        if not Request.objects.filter(status = 'Черновик').first():
            draft_request = {'request_id': 0}
        else:
            draft_request = Request.objects.get(status = 'Черновик')
        draft = DraftSerializer(draft_request)
        serializer = self.serializer_class(data, many=True)
        req = {
            "draft" : draft.data,
            "phenomens" : serializer.data
        }
        return Response(req)
    
    @permission_classes([IsAuth])
    @swagger_auto_schema(request_body=serializer_class)
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class Phenom(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    model_class = Phenomens
    serializer_class = PhenomensSerializer

    def get(self, request, id, format=None):
        """
        Возвращает информацию о природном явлении
        """ 
        if not self.model_class.objects.filter(phenom_id=id).exists():
            return Response(f"Природного явления с таким id не существует")
        phenom = self.model_class.objects.get(phenom_id=id)   
        serializer = self.serializer_class(phenom)
        return Response(serializer.data)
    
    @permission_classes([IsAdmin])
    #@swagger_auto_schema(request_body=serializer_class)
    def put(self, request, id, format=None):
        """
        Обновляет информацию о природном явлении
        """
        phenom = get_object_or_404(self.model_class, phenom_id=id)
        serializer = self.serializer_class(phenom, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @api_view(['Post'])
    @permission_classes([IsAdmin])
    def delete(self, request, id, format=None):
        """
        Меняет статус природного явления на Удален
        """
        phenom = get_object_or_404(self.model_class, phenom_id=id)
        phenom.status = 'Удален'
        phenom.save()
        client.remove_object('images', f'{id}.jpg')
        return Response(status=status.HTTP_200_OK)

@api_view(['Post'])
@permission_classes([IsAuth])
def add_image(request, id):
    phenom = Phenomens.objects.get(phenom_id=id)
    image = (request.FILES['file']).read()
    image_stream = io.BytesIO(image)
    if (image):
        print("картинка есть")
        img_name = f"{id}.png"
        # Загружаем изображение в Minio
        client.put_object('images',
                        img_name,
                        image_stream,
                        len(image))
        phenom.image = f"http://localhost:9000/images/{img_name}"
        phenom.save()
        return Response("Картинка загружена")
    else: 
        phenom.image = f"http://localhost:9000/images/1.png"
        phenom.save()
        return Response("Нет картинки")
    #return Response({"error": str(e)})
    
#@swagger_auto_schema(method='post', request_body=PhenomRecordSerializer)
@api_view(['Post'])
@permission_classes([IsCreator])
def add_phenom_to_request(request, id):
    """
    добавление явления в заявку
    """
    input_request = Request.objects.filter(status='Черновик').first()
    input_phenom = Phenomens.objects.get(phenom_id=id)
    phenom_value = request.data.get('value')
    
    if (input_request):
        if (input_request.status == 'Черновик'):
            new_record = PhenomRecord.objects.create(phenom = input_phenom, request = input_request, value = phenom_value)
            return Response(input_request.request_id)
        else:
            return Response({'error': 'Заявка должна быть черновиком'}, status=status.HTTP_403_FORBIDDEN)
    else:
        ssid = request.COOKIES.get("session_id", None)
        try:
            email = session_storage.get(ssid).decode('utf-8')
            User = Users.objects.get(email=email)
        except: return Response('Сессия не найдена')
        new_request = Request.objects.create(
            user = User,
            request_data = date.today(),
            status = 'Черновик',
            create_date = timezone.now(),
        )
        new_record = PhenomRecord.objects.create(phenom = input_phenom, request = new_request, value = phenom_value)
        #serializer = PhenomRecordSerializer(new_record)
        return Response(new_request.request_id)

class RequestList(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuth]
    model_class = Request
    serializer_class = RequestSerializer

    def get(self, request, format=None):
        """
        Возвращает информацию о заявках
        """
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        status = request.GET.get('status')
        req = self.model_class.objects.exclude(status='Удален')
        ssid = request.COOKIES["session_id"]
        try:
            email = session_storage.get(ssid).decode('utf-8')
            current_user = Users.objects.get(email=email)
        except: return Response('Сессия не найдена')

        if (current_user.is_superuser == False):
            req = req.filter(user=current_user)
            if not req:
                return Response('У польльзователя нет заявок')
        else: req = req.exclude(status='Черновик')


        if start_date:
            req = req.filter(create_date__gte=start_date)
        if end_date:
            req = req.filter(create_date__lte=start_date)
        if status:
            req = req.filter(status=status)
        

        serializer = self.serializer_class(req.all(), many=True)
        tmp = serializer.data
        for i, wa in enumerate(serializer.data):
            user = get_object_or_404(Users, user_id=wa['user'])
            tmp[i]['user'] = '{} {}'.format(user.user_name, user.user_surname)
           
            if wa['moderator'] is None:
                tmp[i]['moderator'] = 'нет'
            else:  
                moderator = Users.objects.get(user_id=wa['moderator'])
                tmp[i]['moderator'] = '{} {}'.format(moderator.user_name, moderator.user_surname)
        print(serializer.data)
        return Response(serializer.data)
    

class RequestDetail(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuth]
    model_class = Request
    serializer_class = RequestSerializer
    ##record_class = PhenomRecord
    record_serial = PhenomRecordSerializer

    def get(self, request, id, format=None):
        """
        Возвращает информацию о заявкe
        """
        req = self.model_class.objects.exclude(status='Удален').filter(request_id=id)
        if (req):
            serializer = self.record_serial(req, many=True)
            tmp = serializer.data[0]
            print(tmp['user'])
            user = get_object_or_404(Users, user_id=tmp['user'])
            tmp['user'] = '{} {}'.format(user.user_name, user.user_surname)
            if tmp['moderator'] is None:
                tmp['moderator'] = 'нет'
            else:  
                moderator = Users.objects.get(user_id=tmp['moderator'])
                tmp['moderator'] = '{} {}'.format(moderator.user_name, moderator.user_surname)
            for r in (tmp['phenomens']):
                print(r['phenom_id'])
                phen = Phenomens.objects.get(phenom_id = r['phenom_id'])
                record = PhenomRecord.objects.get(phenom = phen, request=req[0])
                print(record)
                r['value'] = record.value
            return Response(tmp)
        else: Response({'error': 'Такой заявки нет'}, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, id, format=None):
        """
        Обновляет информацию о заявке
        """
        req = get_object_or_404(self.model_class, request_id=id)
        serializer = self.serializer_class(req, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, id, format=None):
        """
        Меняет статус заявки на Удален
        """
        req = get_object_or_404(self.model_class, request_id=id)
        req.status = 'Удален'
        req.save()
        return Response(status=status.HTTP_200_OK)

#температура 
@api_view(['Put'])
@permission_classes([IsAsync])
def request_async(request, id):
    data = json.loads(request.body)
    print(data["temperature"])
    req = get_object_or_404(Request, request_id=id)
    req.temperature = data["temperature"]
    serializer = RequestSerializer(req, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    else: return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#отклоняет, завершает
@api_view(['Put'])
@permission_classes([IsAdmin])
def moderator_change_status(request, id):
    """
    модератор ставит статусы: Отклонен, Завершен
    """
    req = get_object_or_404(Request, request_id=id)
    current_status = req.status
    input_status = request.data.get("status")
    ssid = request.COOKIES.get("session_id", None)
    try:
        email = session_storage.get(ssid).decode('utf-8')
        current_user = Users.objects.get(email=email)
    except:
        return Response('Сессия не найдена')
    if (current_status == 'Сформирован'):
        if (input_status == 'Отклонен' or input_status == 'Завершен'):
            req.status = input_status
            req.moderator = current_user
            req.end_date = timezone.now()
            req.save()
        else:
            return Response({'error': 'Статус должен быть изменен на Отклонен или Завершен'}, status=status.HTTP_403_FORBIDDEN)
    else:
        return Response({'error': 'Заявка должна быть сформирована, чтобы модератор мог изменить статус'}, status=status.HTTP_403_FORBIDDEN)
    serializer = RequestSerializer(req, partial=True)
    return Response(serializer.data)

#черновик, сформирван, удален
@api_view(['Put'])
@permission_classes([IsCreator])
def creator_change_status(request, id):
    """
    создатель ставит статусы: Черновик, Сформирован
    """
    #statuses = ['Черновик', 'Сформирован']
    ssid = request.COOKIES["session_id"]
    print(ssid)
    try:
        email = session_storage.get(ssid).decode('utf-8')
        current_user = Users.objects.get(email=email)
    except:
        return Response('Сессия не найдена')
    req = get_object_or_404(Request, request_id=id)
    if (current_user == req.user):
        current_status = req.status
        input_status = request.data.get("status")
        if (input_status == 'Удален' or input_status == 'Сформирован'):
            # if (input_status == 'Сформирован'):
            if (current_status == 'Черновик'):
                req.status = input_status
                req.approve_date = timezone.now()

                #данные для асинхронного сервиса
                data = {'id': req.request_id}
                # Отправка POST-запроса на сервис
                response = requests.post(go_url, data=data)
                print(response.status_code)
            # elif (input_status == 'Удален'):
            #     if (current_status == 'Отклонен'):
            #         req.status = input_status
            req.save()
            serializer = RequestSerializer(req, partial=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print(current_user)
            print(req.user)
            return Response({'error': 'Статус должен быть изменен на Удален, Сформирован или Черновик'}, status=status.HTTP_403_FORBIDDEN)
    return Response('Пользователь пытается изменить статус чужой заявки')

#{"status" : "Сформирован"}

@api_view(['Put'])
@permission_classes([IsCreator])
def edit_value(request, id, req_id):
    ssid = request.COOKIES["session_id"]
    req = Request.objects.get(request_id = req_id)
    try:
        email = session_storage.get(ssid).decode('utf-8')
        current_user = Users.objects.get(email=email)
        print(email)
    except:
        return Response('Сессия не найдена')
    if (current_user.user_id == req.user.user_id):
        phenom = Phenomens.objects.get(phenom_id = id)
        record = PhenomRecord.objects.get(phenom = phenom, request=req)
        print(request.data['pvalue'])
        record.value = request.data['pvalue']
        record.save(update_fields=['value'])
        #serializer = PhenomRecordSerializer(record, partial=True)
        #return Response(serializer.data)\
        return Response('Ok')
    else: 
        print('email: {}'.format(email))
        print('cur.user_id: {}, req.user{}'.format(current_user.user_id, req.user))
        return Response('Пользователь не является создателем этой заявки')

@api_view(['Delete'])
@permission_classes([IsCreator])
def delete_record(request, id, req):
    phenom = Phenomens.objects.get(phenom_id = id)
    req = Request.objects.get(request_id = req)
    record = PhenomRecord.objects.get(phenom = phenom, request=req)
    record.delete()
    return Response(status=status.HTTP_200_OK)

class UserViewSet(viewsets.ModelViewSet):
    queryset = Users.objects.all()
    serializer_class = UserSerializer
    model_class = Users
    authentication_classes = []
    permission_classes = [AllowAny]

    def create(self, request):
        print('req is', request.data)
        if self.model_class.objects.filter(email=request.data['email']).exists():
            return Response({'status': 'Exist'}, status=400)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            self.model_class.objects.create_user(
                                     user_name=serializer.data['user_name'],
                                     user_surname=serializer.data['user_surname'],
                                     password=serializer.data['password'],
                                     email=serializer.data['email'],
                                     is_superuser=serializer.data['is_superuser'],
                                     is_staff=serializer.data['is_staff'])
            random_key = str(uuid.uuid4())
            session_storage.set(random_key, serializer.data['email'])
            user_data = {
                "email": request.data['email'],
                "user_name": request.data['user_name'],
                "user_surname": request.data['user_surname'],
                "is_superuser": request.data['is_superuser']
            }

            print('user data is ', user_data)
            response = Response(user_data, status=status.HTTP_201_CREATED)
            # response = HttpResponse("{'status': 'ok'}")
            response.set_cookie("session_id", random_key)
            return response
        return Response({'status': 'Error', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
@swagger_auto_schema(method='post', request_body=UserLoginSerializer)
@api_view(['Post'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('email')
    password = request.data.get('password')
    user = authenticate(request, email=username, password=password)
    
    if user is not None:
        print(user)
        random_key = str(uuid.uuid4())
        session_storage.set(random_key, username)
        user_data = {
            "email": user.email,
            "user_name": user.user_name,
            "user_surname": user.user_surname,
            "password": user.password,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
        }
        response = Response(user_data, status=status.HTTP_201_CREATED)
        response.set_cookie("session_id", random_key)
        return response
    else:
        return HttpResponse("you are not registred", status=400)

@api_view(['POST'])
@permission_classes([IsAuth])
def logout_view(request):
    ssid = request.COOKIES["session_id"]
    if session_storage.exists(ssid):
        session_storage.delete(ssid)
        response_data = {'status': 'Success'}
    else:
        response_data = {'status': 'Error', 'message': 'Session does not exist'}
    return Response(response_data)