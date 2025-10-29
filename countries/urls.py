from django.urls import path
from .views import RefreshCountriesView, CountriesListView, CountryDetailView, StatusView, CountryImageView

urlpatterns = [
    path('countries/refresh', RefreshCountriesView.as_view(), name='countries-refresh'),
    path('countries', CountriesListView.as_view(), name='countries-list'),
    path('countries/image', CountryImageView.as_view(), name='countries-image'),
    path('countries/<str:name>', CountryDetailView.as_view(), name='country-detail'),
    path('status', StatusView.as_view(), name='status'),
]
