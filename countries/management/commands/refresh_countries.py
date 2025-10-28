from django.core.management.base import BaseCommand
from countries.refresh import do_refresh


class Command(BaseCommand):
    help = 'Refresh countries cache from external APIs and generate summary image'


    def handle(self, *args, **options):
        result = do_refresh()
        if result.get('error'):
            self.stdout.write(self.style.ERROR(str(result)))
        else:
            self.stdout.write(self.style.SUCCESS('Refresh complete'))