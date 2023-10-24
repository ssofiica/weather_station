from . import models
from rest_framework import serializers


class PhenomensSerializer(serializers.ModelSerializer):
    class Meta:
        # Модель, которую мы сериализуем
        model = models.Phenomens
        # Поля, которые мы сериализуем
        fields = "__all__"

class RequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Request
        fields = "__all__"

class PhenomRecordSerializer(serializers.ModelSerializer):
    request = RequestSerializer()
    phenom = PhenomensSerializer()
    class Meta:
        model = models.PhenomRecord
        fields = "__all__"

class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Users
        fields = "__all__"
