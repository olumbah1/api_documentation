from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import Country
from .serializers import CountrySerializer
from . import services
from django.http import FileResponse, JsonResponse
import os
from django.conf import settings
from django.db.models import Q

class RefreshCountriesView(APIView):
    """
    POST /countries/refresh
    Fetch countries + exchange rates, then upsert into DB and generate summary image.
    """

    def post(self, request):
        # Step 1: fetch both external sources first (fail early)
        try:
            countries_data = services.fetch_countries()
        except RuntimeError as e:
            return Response({"error": "External data source unavailable", "details": str(e)}, status=503)
        try:
            exchange_rates = services.fetch_exchange_rates()
        except RuntimeError as e:
            return Response({"error": "External data source unavailable", "details": str(e)}, status=503)

        # Step 2: all external data is present — perform DB writes in transaction
        now = timezone.now()
        try:
            with transaction.atomic():
                for c in countries_data:
                    name = c.get('name')
                    capital = c.get('capital')
                    region = c.get('region')
                    population = c.get('population') or 0
                    flag_url = c.get('flag') or c.get('flags')  # restcountries has variants; fallback
                    currencies = c.get('currencies') or []

                    # per spec: if currencies empty, currency_code = null, exchange_rate = null, estimated_gdp = 0
                    if not currencies:
                        currency_code = None
                        exchange_rate = None
                        estimated_gdp = 0
                    else:
                        # use first currency in array
                        first = currencies[0]
                        currency_code = first.get('code')
                        # if currency_code not in exchange_rates => set exchange_rate=None, estimated_gdp=None
                        exchange_rate = exchange_rates.get(currency_code) if currency_code else None
                        if exchange_rate is None:
                            estimated_gdp = None
                        else:
                            estimated_gdp = services.compute_estimated_gdp(population, exchange_rate)

                    # upsert (case-insensitive match on name)
                    obj, created = Country.objects.update_or_create(
                        name__iexact=name,
                        defaults={
                            'name': name,
                            'capital': capital,
                            'region': region,
                            'population': population,
                            'currency_code': currency_code,
                            'exchange_rate': exchange_rate,
                            'estimated_gdp': estimated_gdp,
                            'flag_url': flag_url,
                            'last_refreshed_at': now
                        },
                        # fallback: update_or_create does not accept name__iexact in kwargs, handle manually below
                    )
                # NOTE: Django's update_or_create doesn't support __iexact in lookup dict.
                # We'll implement a manual case-insensitive upsert below instead.
        except Exception as e:
            # If anything goes wrong (DB write), return 500 and rollback (transaction.atomic handles this)
            return Response({"error": "Internal server error"}, status=500)

        # The actual manual upsert implementation (replace the above block)
        # We'll do it cleanly now:
        try:
            with transaction.atomic():
                for c in countries_data:
                    name = c.get('name')
                    capital = c.get('capital')
                    region = c.get('region')
                    population = c.get('population') or 0
                    flag_url = c.get('flag') or c.get('flags')
                    currencies = c.get('currencies') or []

                    if not currencies:
                        currency_code = None
                        exchange_rate = None
                        estimated_gdp = 0
                    else:
                        first = currencies[0]
                        currency_code = first.get('code')
                        exchange_rate = exchange_rates.get(currency_code) if currency_code else None
                        if exchange_rate is None:
                            estimated_gdp = None
                        else:
                            estimated_gdp = services.compute_estimated_gdp(population, exchange_rate)

                    # case-insensitive match
                    existing = Country.objects.filter(name__iexact=name).first()
                    if existing:
                        existing.capital = capital
                        existing.region = region
                        existing.population = population
                        existing.currency_code = currency_code
                        existing.exchange_rate = exchange_rate
                        existing.estimated_gdp = estimated_gdp
                        existing.flag_url = flag_url
                        existing.last_refreshed_at = now
                        existing.save()
                    else:
                        Country.objects.create(
                            name=name,
                            capital=capital,
                            region=region,
                            population=population,
                            currency_code=currency_code,
                            exchange_rate=exchange_rate,
                            estimated_gdp=estimated_gdp,
                            flag_url=flag_url,
                            last_refreshed_at=now
                        )
                # save global last_refreshed somewhere: easiest is store in a single-row DB or settings.
                # For simplicity we'll use a small cache file to store last refresh time.
                # But we'll also rely on the countries last_refreshed_at.
        except Exception as e:
            return Response({"error": "Internal server error"}, status=500)

        # Generate summary image:
        # Get total and top 5 by estimated_gdp (descending), handle nulls such that None are treated as lowest
        total = Country.objects.count()
        top5_qs = Country.objects.exclude(estimated_gdp__isnull=True).order_by('-estimated_gdp')[:5]
        top5 = [{
            'name': c.name,
            'estimated_gdp': c.estimated_gdp
        } for c in top5_qs]
        # If fewer than 5 with estimated_gdp, include Null ones as N/A
        if len(top5) < 5:
            needed = 5 - len(top5)
            nulls = Country.objects.filter(estimated_gdp__isnull=True)[:needed]
            for c in nulls:
                top5.append({'name': c.name, 'estimated_gdp': None})

        try:
            services.generate_summary_image(total=total, top5=top5, timestamp=now, out_path=settings.SUMMARY_IMAGE_PATH)
        except Exception as e:
            # image generation failure does not require rollback of DB writes per spec.
            # But return success with image generation failure noted.
            return Response({
                "message": "Refresh successful but failed to generate summary image",
                "error": str(e)
            }, status=200)

        return Response({"message": "Refresh successful", "total_countries": total, "last_refreshed_at": now}, status=200)


class CountriesListView(APIView):
    """
    GET /countries  -> supports ?region= & ?currency= & ?sort=gdp_desc
    """

    def get(self, request):
        qs = Country.objects.all()
        region = request.query_params.get('region')
        currency = request.query_params.get('currency')
        sort = request.query_params.get('sort')

        if region:
            qs = qs.filter(region__iexact=region)
        if currency:
            qs = qs.filter(currency_code__iexact=currency)

        if sort == 'gdp_desc':
            qs = qs.order_by('-estimated_gdp')
        elif sort == 'gdp_asc':
            qs = qs.order_by('estimated_gdp')

        serializer = CountrySerializer(qs, many=True)
        return Response(serializer.data, status=200)


class CountryDetailView(APIView):
    """
    GET /countries/<name>
    DELETE /countries/<name>
    """

    def get_object(self, name):
        obj = Country.objects.filter(name__iexact=name).first()
        if not obj:
            return None
        return obj

    def get(self, request, name):
        obj = self.get_object(name)
        if not obj:
            return Response({"error": "Country not found"}, status=404)
        serializer = CountrySerializer(obj)
        return Response(serializer.data, status=200)

    def delete(self, request, name):
        obj = self.get_object(name)
        if not obj:
            return Response({"error": "Country not found"}, status=404)
        obj.delete()
        return Response({"message": "Country deleted"}, status=200)


class StatusView(APIView):
    """
    GET /status
    """
    def get(self, request):
        total = Country.objects.count()
        # last_refreshed_at = most recent timestamp among countries
        last = Country.objects.order_by('-last_refreshed_at').first()
        last_ts = last.last_refreshed_at if last else None
        return Response({
            "total_countries": total,
            "last_refreshed_at": last_ts
        }, status=200)


class CountryImageView(APIView):
    """
    GET /countries/image
    """
    def get(self, request):
        path = settings.SUMMARY_IMAGE_PATH
        if not os.path.exists(path):
            return Response({"error": "Summary image not found"}, status=404)
        return FileResponse(open(path, 'rb'), content_type='image/png')
