
from cashonly.models import *
from django.conf import settings
from django.core.mail import send_mass_mail
from django.core.management.base import NoArgsCommand
from django.template import Context
from django.template.loader import get_template
from django.utils import translation
from django.utils.translation import ugettext as _

class Command(NoArgsCommand):
	help = 'Sends a reminder mail to every with a negative credit'

	def handle_noargs(self, **options):
		translation.activate('de')

		tpl = get_template('cashonly/debt_reminder.txt')

		messages = []
		for a in Account.objects.all():
			if a.credit < 0:
				name = '%s %s' % (a.user.first_name, a.user.last_name)
				context = {'name': name, 'credit': a.credit}
			
				rcpts = ['%s <%s>' % (name, a.user.email)]

				messages.append(('%s%s' % (settings.EMAIL_SUBJECT_PREFIX,
				                 _('Debt Reminder')),
				                 tpl.render(Context(context)),
				                 settings.DEFAULT_FROM_EMAIL, rcpts))

		send_mass_mail(tuple(messages))
