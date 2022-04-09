from django.utils import timezone


def year(request):
    return {
        'year': int(timezone.now().strftime('%Y'))
    }
