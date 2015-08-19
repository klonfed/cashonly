from django.contrib.auth.models import User
from cashonly.models import Account

class CashBackend(object):
	def authenticate(self, card_number=None, pin=None):
		if not card_number.isdigit():
			raise ValueError('card_number has to consist of digits only!')

		if len(pin) > 0 and not pin.isdigit():
			raise ValueError('pin has to consist of digits only or \
			    has to be empty!')

		try:
			account = Account.objects.get(card_number=card_number)
		except Account.DoesNotExist:
			return None

		if account.check_pin(pin):
			return account.user

		return None
