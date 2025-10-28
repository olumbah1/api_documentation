from django.contrib import admin
from .models import Country

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name','region','currency_code','population','estimated_gdp','last_refreshed_at')
    search_fields = ('name','currency_code')
