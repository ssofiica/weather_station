from django.contrib import admin
from . import models

admin.site.register(models.Phenomens)
admin.site.register(models.Users)
admin.site.register(models.Request)
admin.site.register(models.PhenomRecord)
