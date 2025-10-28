
import requests
from django.utils import timezone
from .models import Country
from .utils.image import generate_summary_image
from django.db import transaction

COUNTRIES_URL = 'https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies'
EXCHANGE_URL = 'https://open.er-api.com/v6/latest/USD'


def do_refresh(timeout=20):
    try:
        c_resp = requests.get(COUNTRIES_URL, timeout=timeout)
        e_resp = requests.get(EXCHANGE_URL, timeout=timeout)
        c_resp.raise_for_status()
        e_resp.raise_for_status()
    except requests.RequestException as exc:
        # determine which API failed by message
        url = getattr(exc.response, 'url', None) if hasattr(exc, 'response') else None
        api_name = 'External API'
        if url and 'restcountries' in url:
            api_name = 'Countries API'
        elif url and 'open.er-api' in url:
            api_name = 'Exchange API'
        return {'error': 'External data source unavailable', 'details': f'Could not fetch data from {api_name}'}

    countries_data = c_resp.json()
    exchange_data = e_resp.json()
    rates = exchange_data.get('rates', {})

    now = timezone.now()

    # Use transaction to avoid partial updates
    try:
        with transaction.atomic():
            for c in countries_data:
                name = c.get('name')
                capital = c.get('capital') or None
                region = c.get('region') or None
                population = int(c.get('population') or 0)
                flag_url = c.get('flag') or None

                currencies = c.get('currencies') or []
                currency_code = None
                if isinstance(currencies, list) and len(currencies) > 0:
                    currency = currencies[0]
                    currency_code = currency.get('code') if currency else None

                exchange_rate = None
                estimated_gdp = None

                if not currency_code:
                    exchange_rate = None
                    estimated_gdp = 0
                else:
                    if currency_code in rates:
                        exchange_rate = float(rates[currency_code])
                        multiplier = __import__('random').uniform(1000,2000)
                        estimated_gdp = population * multiplier / exchange_rate
                    else:
                        exchange_rate = None
                        estimated_gdp = None

                # case-insensitive match
                try:
                    existing = Country.objects.get(name__iexact=name)
                except Country.DoesNotExist:
                    existing = None

                if existing:
                    existing.name = name
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

        # After commit: generate image
        total = Country.objects.count()
        top5_qs = Country.objects.exclude(estimated_gdp__isnull=True).order_by('-estimated_gdp')[:5]
        top5 = [{'name': c.name, 'estimated_gdp': c.estimated_gdp} for c in top5_qs]
        timestamp = now.isoformat()
        generate_summary_image(total, top5, timestamp)

        return {'message': 'Refresh complete', 'total_countries': total, 'last_refreshed_at': timestamp}
    except Exception as exc:
        return {'error': 'Internal server error'}

