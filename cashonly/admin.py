from django.contrib import admin
from cashonly.models import *
from cashonly.formfields import DigitField
from django import forms
from django.template.defaultfilters import escape
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy
from django.utils.translation import ugettext_noop

class AccountForm(forms.ModelForm):
	credit_change = forms.DecimalField(max_digits=5, decimal_places=2,
	                                   required=False,
	                                   label=ugettext_lazy('amount'))

	credit_change_comment = forms.CharField(max_length=64, required=False,
	                                        label=ugettext_lazy('comment'))

	#pin_change = forms.RegexField(regex='^\d{4,}$', required=False,
	#                            label=ugettext_lazy('PIN'))
	pin_change = DigitField(min_length=4, required=False,
	                            label=ugettext_lazy('PIN'))

	pin_empty = forms.BooleanField(required=False,
	                              label=ugettext_lazy('clear PIN'))

	class Meta:
		model = Account

		# Include all fields (omitting this causes a RemovedInDjango18Warning)
		exclude = []

class AccountAdmin(admin.ModelAdmin):
	list_display = ('user', 'card_number', 'credit', 'transaction_link')
	form = AccountForm
	readonly_fields = ('user', 'credit',)
	fieldsets = (
	    (None, {
	        'fields': ('user', 'card_number', 'credit'),
	    }),
	    (ugettext_lazy('credit change'), {
	        'fields': ('credit_change', 'credit_change_comment'),
	    }),
		(ugettext_lazy('change PIN'), {
		    'fields': ('pin_change', 'pin_empty'),
		}),
	)

	# Disable manual creation of accounts.
	# Accounts are create after user creation automatically.
	def has_add_permission(self, request):
		return False

	def transaction_link(self, account):
		return '<a href="%s?account__id__exact=%d">%s</a>' % \
		    (reverse("admin:cashonly_transaction_changelist"), account.id,
		     _('Transactions'))

	transaction_link.short_description = ugettext_lazy('Transaction link')

	transaction_link.allow_tags = True

	def save_model(self, request, obj, form, change):
		pin = form.cleaned_data['pin_change']
		pin_empty = form.cleaned_data['pin_empty']

		if pin_empty:
			obj.clear_pin()
		else:
			if pin is not None and len(pin) != 0:
				obj.set_pin(pin)

		PAYOUT_SUBJECT = ugettext_noop('Payout')
		DEPOSIT_SUBJECT = ugettext_noop('Deposit')
		DESCRIPTION = ugettext_noop('Authorized by %(first)s %(last)s')

		amount = form.cleaned_data['credit_change']
		comment = form.cleaned_data['credit_change_comment']

		if amount is not None and amount != 0:
			if amount > 0:
				subject = DEPOSIT_SUBJECT
			else:
				subject = PAYOUT_SUBJECT

			desc = DESCRIPTION % {'first': request.user.first_name,
			                      'last': request.user.last_name}
			if comment is not None and len(comment) > 0:
				desc += ' (%s)' % (comment)
			obj.change_credit(aount, subject, desc)

		# Make sure the object is saved in any case
		obj.save()


class ProductBarcodeInline(admin.TabularInline):
	model = ProductBarcode
	extra = 1

class ProductAdmin(admin.ModelAdmin):
	list_display = ('name', 'category', 'price', 'active')
	list_filter = ['category', 'active']
	ordering = ('-active', 'name')
	inlines = [ProductBarcodeInline]
	fields = ('name', 'price', 'active', 'category', 'image')

class ProductCategoryAdmin(admin.ModelAdmin):
	list_display = ('name', 'comment')

class SalesLogEntryAdmin(admin.ModelAdmin):
	list_display = ('account', 'timestamp', 'product', 'count', 'unit_price')
	list_filter = ['account', 'timestamp', 'product']
	# Make sales log entries completely read-only
	readonly_fields = map(lambda f: f.name, SalesLogEntry._meta.fields)

class TransactionAdmin(admin.ModelAdmin):
	list_display = ('account', 'timestamp', 'subject', 'description', 'amount')
	list_filter = ['account', 'timestamp', 'subject']

	# Disable mass deletion in the overview page
	actions = None

	date_hierarchy = 'timestamp'

	# Disable tampering with the transactions completely.
	def has_add_permission(self, request):
		return False
	def has_change_permission(self, request, obj=None):
		if obj is None:
			return True
		return False
	def has_delete_permission(self, request, obj=None):
		return False

	# Needed to not trigger an ImproperlyConfigured exception.
	# FIXME: a bit too hacky
	def changelist_view(self, request, extra_context=None):
		self.list_display_links = (None, )
		return super(TransactionAdmin, self).changelist_view(request,
		                                                     extra_context=None)

admin.site.register(Account, AccountAdmin)
admin.site.register(Product, ProductAdmin)
#admin.site.register(ProductBarcode)
admin.site.register(ProductCategory, ProductCategoryAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(SalesLogEntry, SalesLogEntryAdmin)

