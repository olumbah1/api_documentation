# countries/management/commands/refresh_countries.py
from django.core.management.base import BaseCommand
from rest_framework.test import APIRequestFactory
# import from your app 'countries' (not country_app)
from countries.views import RefreshCountriesView

class Command(BaseCommand):
    help = 'Refresh countries from external APIs'

    def handle(self, *args, **options):
        factory = APIRequestFactory()
        request = factory.post('/countries/refresh')
        view = RefreshCountriesView.as_view()
        response = view(request)
        # response may be a DRF Response instance or a Django HttpResponse
        try:
            data = getattr(response, 'data', None) or response.content
        except Exception:
            data = str(response)
        self.stdout.write(str(data))
