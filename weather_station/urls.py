from django.contrib import admin
from app import views
from django.urls import include, path
from rest_framework import routers
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

router = routers.DefaultRouter()

schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)
router.register(r'user', views.UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    #методы для природных явлений (услуг)
    path(r'phenomens/', views.PhenomensList.as_view(), name='get_phenomens'),
    #внтури методы get, post, delete, put
    path(r'phenomens/<int:id>/', views.Phenom.as_view(), name='phenom_methods'),
    path(r'phenomens/add/<int:id>/', views.add_phenom_to_request, name='add_phenom_to_request'),
    path(r'phenomens/add_image/<int:id>/', views.add_image, name='add_image'),

    # #методы для заявок
    path(r'requests/', views.RequestList.as_view(), name='get_requests'),
    path(r'requests/<int:id>/', views.RequestDetail.as_view(), name='request_methods'),
    path(r'requests/<int:id>/moderator_change_status/', views.moderator_change_status, name='moderator_change_status'),
    path(r'requests/<int:id>/creator_change_status/', views.creator_change_status, name='creator_change_status'),
    path(r'requests/temperature/<int:id>/', views.request_async, name='async'),

    # #методы для заявок
    path(r'phenom_record/edit_value/<int:id>/<int:req>/', views.edit_value, name='edit_value'),
    path(r'phenom_record/delete/<int:id>/<int:req>/', views.delete_record, name='delete_record'),
    
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('login/',  views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('admin/', admin.site.urls),
]
