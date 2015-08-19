from cashonly.models import *
from django.conf import settings
from django.core.mail import send_mass_mail
from django.core.management.base import NoArgsCommand, CommandError
from django.template import Context
from django.template.loader import get_template
from django.utils import translation
from django.utils.dateformat import DateFormat
from django.utils.formats import get_format
from django.utils.translation import ugettext as _
import datetime

RANGE = 24
USERSETTINGS_URL = 'https://cypher/kasse/usersettings/'

class Command(NoArgsCommand):
	help = 'Sends out the daily digest to all users with transactions' + \
	       'in the last %dh' % RANGE

	def handle_noargs(self, **options):
		translation.activate('de')

		tpl = get_template('cashonly/daily_digest.txt')

		messages = []
		for a in Account.objects.all():
			name = '%s %s' % (a.user.first_name, a.user.last_name)
			context = {'name': name,
			           'credit': a.credit,
					   'range': RANGE,
					   'url': USERSETTINGS_URL}

			transactions = Transaction.objects.filter(account = a) \
			    .filter(timestamp__gte=(datetime.datetime.now()
			        - datetime.timedelta(hours = RANGE)))

			if transactions.count() > 0:
				lengths = {'timestamp': len(_('date')),
				           'description': len(_('subject')),
				           'amount': len(_('amount'))}

				sum = 0
				for t in transactions:
					lengths['timestamp'] = \
					    max(lengths['timestamp'], len(DateFormat(t.timestamp) \
					    .format(get_format('SHORT_DATETIME_FORMAT'))))
					lengths['description'] = \
					    max(lengths['description'], len(t.description))
					lengths['amount'] = \
					    max(lengths['amount'], len(str(t.amount)))
					t.description = t.description.split('\n')

					sum += t.amount

				lengths['sum'] = lengths['timestamp'] + \
				    lengths['description'] + lengths['amount']
				context['lengths'] = lengths
				context['tl'] = transactions
				context['sum'] = sum

				rcpts = ['%s <%s>' % (name, a.user.email)]

				messages.append(('%s%s' % (settings.EMAIL_SUBJECT_PREFIX,
				                 _('Account Statement')),
				                 tpl.render(Context(context)),
				                 settings.DEFAULT_FROM_EMAIL, rcpts))

		send_mass_mail(tuple(messages))
