from rest_framework import serializers
from .models import Country

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = [
            'id',
            'name',
            'capital',
            'region',
            'population',
            'currency_code',
            'exchange_rate',
            'estimated_gdp',
            'flag_url',
            'last_refreshed_at',
        ]

    def validate(self, data):
        """
        Validate required fields. Raises serializers.ValidationError with the
        exact error format your spec requested.
        """
        errors = {}
        # For creation (no instance) ensure required fields exist
        if getattr(self, 'instance', None) is None and not data.get('name'):
            errors['name'] = 'is required'
        # population key must exist and not be None
        if 'population' in data and data['population'] is None:
            errors['population'] = 'is required'
        if getattr(self, 'instance', None) is None and not data.get('currency_code'):
            errors['currency_code'] = 'is required'

        if errors:
            # This matches the JSON structure you asked for:
            # { "error": "Validation failed", "details": { ... } }
            raise serializers.ValidationError({'error': 'Validation failed', 'details': errors})
        return data
