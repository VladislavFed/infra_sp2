from django.forms import ValidationError
from django.utils import timezone


def title_year_validator(value):
    current_year = timezone.now().year

    if 0 > value > current_year:
        raise ValidationError(
            'Год обязан быть между 0 и текущим годом.'
        )
