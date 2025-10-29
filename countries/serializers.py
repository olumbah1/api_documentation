from rest_framework import serializers
from .models import Country

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = [
            'id', 'name', 'capital', 'region', 'population', 'currency_code',
            'exchange_rate', 'estimated_gdp', 'flag_url', 'last_refreshed_at'
        ]
        read_only_fields = ['id', 'exchange_rate', 'estimated_gdp', 'last_refreshed_at']

    def validate(self, data):
        errors = {}
        if not data.get('name'):
            errors['name'] = 'is required'
        if data.get('population') is None:
            errors['population'] = 'is required'
        # currency_code can be None per spec if currencies missing; we don't force it here
        if errors:
            raise serializers.ValidationError(errors)
        return data
