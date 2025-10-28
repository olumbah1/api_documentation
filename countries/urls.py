from django.urls import path
from . import views

urlpatterns = [
    path('countries/refresh', views.refresh_view),
    path('countries/image', views.image_view),
    path('countries', views.countries_list),
    path('countries/<str:name>', views.country_detail),
    path('countries/<str:name>/delete', views.country_delete),
    path('status', views.status_view),
]