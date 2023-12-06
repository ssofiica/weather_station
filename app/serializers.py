from . import models
from rest_framework import serializers
from collections import OrderedDict

class UserSerializer(serializers.ModelSerializer):
    is_staff = serializers.BooleanField(default=False, required=False)
    is_superuser = serializers.BooleanField(default=False, required=False)
    class Meta:
        model = models.Users
        fields = ['user_name','user_surname','email', 'password', 'is_staff', 'is_superuser']

class UserLoginSerializer(serializers.Serializer):
    email = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

class PhenomensSerializer(serializers.ModelSerializer):
    class Meta:
        # Модель, которую мы сериализуем
        model = models.Phenomens
        # Поля, которые мы сериализуем
        fields = "__all__"
        
        def get_fields(self):
            new_fields = OrderedDict()
            for name, field in super().get_fields().items():
                field.required = False
                new_fields[name] = field
            return new_fields 

class DraftSerializer(serializers.Serializer):
    request_id = serializers.IntegerField()

class RequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Request
        fields = "__all__"

class PhenomRecordSerializer(serializers.ModelSerializer):
    phenomens = serializers.SerializerMethodField()

    def get_phenomens(self, obj):
        records = models.PhenomRecord.objects.filter(request=obj)
        #print(records)
        tmp = records.values_list('phenom', flat=True)
        phenoms = models.Phenomens.objects.filter(phenom_id__in = tmp)
        #print(phenoms)
        serializer = PhenomensSerializer(phenoms, many = True)
        return serializer.data

    class Meta:
        model = models.Request
        fields = ('request_id', 'user', 'request_data', 'status', 'create_date', 'approve_date', 'end_date', 'moderator', 'phenomens')


