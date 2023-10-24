from django.contrib import admin
from app import views
from django.urls import include, path
from rest_framework import routers

router = routers.DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    #методы для природных явлений (услуг)
    path(r'phenomens/', views.PhenomensList.as_view(), name='get_phenomens'),
    #внтури методы get, post, delete, put
    path(r'phenomens/<int:id>/', views.Phenom.as_view(), name='phenom_methods'),
    path(r'phenomens/add/<int:id>/<int:req>/', views.add_phenom_to_request, name='add_phenom_to_request'),

    # #методы для заявок
    path(r'requests/', views.RequestList.as_view(), name='get_requests'),
    path(r'requests/<int:id>/', views.RequestDetail.as_view(), name='request_methods'),
    path(r'requests/<int:id>/moderator_change_status/', views.moderator_change_status, name='moderator_change_status'),
    path(r'requests/<int:id>/creator_change_status/', views.creator_change_status, name='creator_change_status'),

    # #методы для заявок
    path(r'phenom_record/edit_value/<int:id>/<int:req>/', views.edit_value, name='edit_value'),
    path(r'phenom_record/delete/<int:id>/<int:req>/', views.delete_record, name='delete_record'),
    
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('admin/', admin.site.urls),
]
