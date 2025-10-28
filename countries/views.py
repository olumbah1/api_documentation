from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Country
from .serializers import CountrySerializer
from .refresh import do_refresh
from django.http import FileResponse, Http404
import os

@api_view(['POST'])
def refresh_view(request):
    result = do_refresh()
    if result.get('error'):
        if 'External data source unavailable' in result.get('error') or 'External data source unavailable' in result.get('details', ''):
            return Response({'error': 'External data source unavailable', 'details': result.get('details')}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(result)

@api_view(['GET'])
def countries_list(request):
    region = request.query_params.get('region')
    currency = request.query_params.get('currency')
    sort = request.query_params.get('sort')

    qs = Country.objects.all()
    if region:
        qs = qs.filter(region=region)
    if currency:
        qs = qs.filter(currency_code=currency)
    if sort == 'gdp_desc':
        qs = qs.order_by('-estimated_gdp')

    serializer = CountrySerializer(qs, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def country_detail(request, name):
    try:
        c = Country.objects.get(name__iexact=name)
    except Country.DoesNotExist:
        return Response({'error': 'Country not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = CountrySerializer(c)
    return Response(serializer.data)

@api_view(['DELETE'])
def country_delete(request, name):
    try:
        c = Country.objects.get(name__iexact=name)
    except Country.DoesNotExist:
        return Response({'error': 'Country not found'}, status=status.HTTP_404_NOT_FOUND)
    c.delete()
    return Response({'message': 'Deleted'})

@api_view(['GET'])
def status_view(request):
    total = Country.objects.count()
    last = Country.objects.order_by('-last_refreshed_at').first()
    return Response({'total_countries': total, 'last_refreshed_at': last.last_refreshed_at if last else None})

@api_view(['GET'])
def image_view(request):
    path = os.path.join(os.getcwd(), 'cache', 'summary.png')
    if not os.path.exists(path):
        return Response({'error': 'Summary image not found'}, status=status.HTTP_404_NOT_FOUND)
    return FileResponse(open(path, 'rb'), content_type='image/png')



