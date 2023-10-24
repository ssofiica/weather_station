from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from app.serializers import PhenomensSerializer
from app.serializers import PhenomRecordSerializer
from app.serializers import RequestSerializer
from app.serializers import UsersSerializer
from app.models import Phenomens
from app.models import PhenomRecord
from app.models import Request
from app.models import Users
from datetime import date
from rest_framework.views import APIView
from rest_framework.decorators import api_view


class PhenomensList(APIView):
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
        serializer = self.serializer_class(data, many=True)
        return Response(serializer.data)
    
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class Phenom(APIView):
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
    
    def put(self, request, id, format=None):
        """
        Обновляет информацию о природном явлении
        """
        phenom = get_object_or_404(self.model_class, phenom_id=id)
        serializer = self.serializer_class(phenom, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id, format=None):
        """
        Меняет статус природного явления на Удален
        """
        phenom = get_object_or_404(self.model_class, phenom_id=id)
        phenom.status = 'Удален'
        phenom.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['Post'])
def add_phenom_to_request(request, id, req):
    """
    добавление явления в заявку
    """

    input_request = Request.objects.get(request_id=req)
    input_phenom = Phenomens.objects.get(phenom_id=id)
    phenom_value = request.data.get('value')
    
    if (input_request):
        if (input_request.status == 'Черновик'):
            new_record = PhenomRecord.objects.create(phenom = input_phenom, request = input_request, value = phenom_value)
        else:
            return Response({'error': 'Заявка должна быть черновиком'}, status=status.HTTP_403_FORBIDDEN)
    else:
        new_request = Request.objects.create(
            user = 2,
            request_data = date.today(),
            status = 'Черновик',
            create_date = date.today(),
            moderator = 1
        )
        new_record = PhenomRecord.objects.create(phenom = input_phenom, request = new_request, value = phenom_value)
    serializer = PhenomRecordSerializer(new_record)
    return Response(serializer.data)

class RequestList(APIView):
    model_class = Request
    serializer_class = RequestSerializer

    def get(self, request, format=None):
        """
        Возвращает информацию о заявках
        """
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        status = request.GET.get('status')
        requests = self.model_class.objects.exclude(status='Удален')
        if start_date:
            requests = requests.filter(create_date__gte=start_date)
            if end_date:
                requests = requests.filter(create_date__lte=start_date)
        if status:
            requests = requests.filter(status=status)
        
        serializer = self.serializer_class(requests.all(), many=True)
        return Response(serializer.data)
    

class RequestDetail(APIView):
    model_class = Request
    serializer_class = RequestSerializer
    record_class = PhenomRecord
    record_serial = PhenomRecordSerializer

    def get(self, request, id, format=None):
        """
        Возвращает информацию о заявкe
        """
        requests = self.model_class.objects.get(request_id=id)
        record = self.record_class.objects.filter(request=requests)
        serializer = self.record_serial(record, many=True)
        return Response(serializer.data)

    def put(self, request, id, format=None):
        """
        Обновляет информацию о природном явлении
        """
        req = get_object_or_404(self.model_class, phenom_id=id)
        serializer = self.serializer_class(req, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#отклоняет, завершает
@api_view(['Put'])
def moderator_change_status(request, id):
    """
    модератор ставит статусы: Отклонен, Завершен
    """
    req = get_object_or_404(Request, request_id=id)
    current_status = req.status
    input_status = request.data.get("status")
    if (current_status == 'Сформирован'):
        if (input_status == 'Отклонен' or input_status == 'Завершен'):
            req.status = input_status
            req.save()
        else:
            return Response({'error': 'Статус должен быть изменен на Отклонен или Завершен'}, status=status.HTTP_403_FORBIDDEN)
    else:
        return Response({'error': 'Заявка должна быть сформирована, чтобы модератор мог изменить статус'}, status=status.HTTP_403_FORBIDDEN)
    serializer = RequestSerializer(req, partial=True)
    return Response(serializer.data)

#черновик, сформирван, удален
@api_view(['Put'])
def creator_change_status(request, id):
    """
    создатель ставит статусы: Черновик, Сформирован, Удален
    """
    #statuses = ['Черновик', 'Сформирован', 'Удален']
    req = get_object_or_404(Request, request_id=id)
    current_status = req.status
    input_status = request.data.get("status")
    if (input_status == 'Черновик' or input_status == 'Сформирован'or input_status == 'Удален'):
        if (input_status == 'Сформирован'):
            if (current_status == 'Черновик'):
                req.status = input_status
        elif (input_status == 'Черновик'):
            if (current_status == 'Отклонен' or current_status == 'Удален'):
                req.status = input_status
        elif (input_status == 'Удален'):
            if (current_status == 'Черновик'):
                req.status = input_status
        req.save()
        return Response(status=status.HTTP_201_CREATED)
    else:
        return Response({'error': 'Статус должен быть изменен на Удален, Сформирован или Черновик'}, status=status.HTTP_403_FORBIDDEN)
    serializer = RequestSerializer(req, partial=True)
    return Response(serializer.data)
#{"status" : "Сформирован"}


@api_view(['Put'])
def edit_value(request, id, req):
    phenom = Phenomens.objects.get(phenom_id = id)
    req = Request.objects.get(request_id = req)
    record = PhenomRecord.objects.get(phenom = phenom, request=req)
    phenom_value = request.data.get('value')
    record.value = phenom_value
    record.save()
    serializer = PhenomRecordSerializer(record, partial=True)
    return Response(serializer.data)

@api_view(['Delete'])
def delete_record(request, id, req):
    phenom = Phenomens.objects.get(phenom_id = id)
    req = Request.objects.get(request_id = req)
    record = PhenomRecord.objects.get(phenom = phenom, request=req)
    record.delete()
    return Response(status=status.HTTP_201_CREATED)