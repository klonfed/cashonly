from django.forms import CharField
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.core.validators import EMPTY_VALUES

class DigitField(CharField):
	def clean(self, value):
		super(DigitField, self).clean(value)

		if value not in EMPTY_VALUES and not value.isdigit():
			raise ValidationError(_('Please enter only digits.'))

		return value
