from django.conf import settings
from django.db import models
from django.core.files import File
from django.contrib.auth.models import User
from django.db.models.signals import pre_save, post_save
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext_noop
from django.db import transaction
import PIL.Image
import StringIO

class Account(models.Model):
	user = models.OneToOneField(User)
	card_number = models.CharField(max_length=32, unique=True, blank=True,
	                               null=True, verbose_name = _('card number'))
	pin = models.CharField(max_length=32, blank=True, verbose_name = _('PIN'))
	daily_digest = models.BooleanField(verbose_name = _('daily digest'), default=True)
	credit = models.DecimalField(max_digits=5, decimal_places=2, default=0,
	                             verbose_name = _('credit'))

	def __unicode__(self):
		return self.user.username

	class Meta:
		verbose_name = _('account')
		verbose_name_plural = _('accounts')

	@receiver(post_save, sender=User)
	def user_post_save_handler(sender, instance, created, **kwargs):
		if created:
			# We don't have ldap_user on creation, so just add the account
			account = Account(user=instance)
			account.save()
		else:
			# When we already have an account,
			# we can add the number form LDAP (mongo shit)
			if hasattr(instance, 'ldap_user') \
			    and instance.ldap_user.attrs.has_key('employeenumber'):
				instance.account.card_number = \
				    instance.ldap_user.attrs['employeenumber'][0]
				instance.account.save()

	@transaction.atomic
	def change_credit(self, amount, subject, desc):
		# For atomicity fetch current value first
		cur = Account.objects.filter(pk=self.pk)[0]
		self.credit = cur.credit + amount
		self.save()

		trans = Transaction(account=self, subject=subject,
						    amount=amount, description=desc)
		trans.save()

	def buy_products(self, products):
		# TODO place it somewhere else
		MAX_DEBIT = -35
		BUY_SUBJECT = ugettext_noop('Purchase')

		if min(products.values()) <= 0:
			raise ValueError('Non-positive amount in products dict.')

		total_value = sum(map(lambda p: p.price * products[p], products.keys()))
		if self.credit - total_value >= MAX_DEBIT:
			desc = ''
			for product in products.keys():
				if not product.active:
					raise ValueError('Trying to buy a disabled product.')
				amount = products[product]

				logentry = SalesLogEntry(account=self, product=product,
				                         count=amount, unit_price=product.price)
				logentry.save()

				desc += '%d x %s\n' % (amount, product.name)

			self.change_credit(-total_value, BUY_SUBJECT, desc)
			return True
		else:
			return False

	def buy_product(self, product, amount=1):
		return self.buy_products({product: amount})

	def set_pin(self, pin):
		# TODO: hash pin
		self.pin = pin
		self.save()

	def clear_pin(self):
		self.pin = ''
		self.save()

	def check_pin(self, pin):
		return pin == self.pin

class ProductCategory(models.Model):
	name = models.CharField(max_length=32, unique=True,
	                        verbose_name = _('name'))
	comment = models.CharField(max_length=128, blank=True,
	                           verbose_name = _('comment'))

	def __unicode__(self):
		return "%s (%s)" % (self.name, self.comment)

	class Meta:
		verbose_name = _('product category')
		verbose_name_plural = _('product categories')

class Product(models.Model):
	name = models.CharField(max_length=32, unique=True,
	                        verbose_name = _('name'))
	price = models.DecimalField(max_digits=5, decimal_places=2,
	                            verbose_name = _('price'))
	active = models.BooleanField(default = True, verbose_name = _('active'))
	category = models.ForeignKey(ProductCategory, blank=True, null=True,
	                             verbose_name = _('category'))
	image = models.ImageField(upload_to="products", verbose_name = _('image'),
	                          blank=True, null=True)
	image_thumbnail = models.ImageField(upload_to="products_thumb",
	                                    verbose_name = _('image'),
	                                    blank=True, null=True)

	def __unicode__(self):
		return self.name

	class Meta:
		verbose_name = _('product')
		verbose_name_plural = _('products')

@receiver(pre_save, sender=Product)
def product_post_save_handler(sender, instance, **kwargs):
	img = instance.image
	if img:
		scaledFile = StringIO.StringIO()
		img.open(mode='r')
		with img:
			scaled = PIL.Image.open(img)
			thumbnail_size = getattr(settings, 'THUMBNAIL_SIZE', (150, 150))
			scaled.thumbnail(thumbnail_size, PIL.Image.ANTIALIAS)
			scaled.save(scaledFile, 'PNG')
		scaledFile.seek(0)

		instance.image_thumbnail.save(img.url, File(scaledFile), save=False)


class ProductBarcode(models.Model):
	barcode = models.CharField(max_length=32, unique=True,
	                           verbose_name = _('barcode'))
	comment = models.CharField(max_length=128, blank=True,
	                           verbose_name = _('comment'))
	product = models.ForeignKey(Product, verbose_name = _('product'))

	def __unicode__(self):
		return self.barcode

	class Meta:
		verbose_name = _('barcode')
		verbose_name_plural = _('barcodes')

class Transaction(models.Model):
	account = models.ForeignKey(Account, verbose_name = _('account'))
	timestamp = models.DateTimeField(auto_now_add=True,
	                                 verbose_name = _('timestamp'))
	subject = models.CharField(max_length=32, verbose_name = _('subject'))
	description = models.TextField(verbose_name = _('description'))
	amount = models.DecimalField(max_digits=5, decimal_places=2,
	                             verbose_name = _('amount'))

	class Meta:
		verbose_name = _('transaction')
		verbose_name_plural = _('transactions')

class SalesLogEntry(models.Model):
	account = models.ForeignKey(Account, verbose_name = _('account'))
	product = models.ForeignKey(Product, verbose_name = _('product'))
	count = models.IntegerField(verbose_name = _('count'))
	unit_price = models.DecimalField(max_digits=5, decimal_places=2,
	                                 verbose_name = _('unit price'))
	timestamp = models.DateTimeField(auto_now_add=True,
	                                 verbose_name = _('timestamp'))

	def __unicode__(self):
		return '%dx %s - %s' % (self.count, self.product, self.account)
	class Meta:
		verbose_name = _('sales log entry')
		verbose_name_plural = _('sales log entries')

@receiver(pre_delete, sender=SalesLogEntry)
def logentry_pre_delete_handler(sender, instance, **kwargs):
	SUBJECT = ugettext_noop('Cancellation')
	DESC = '%d x %s'

	instance.account.change_credit(
	    instance.unit_price * instance.count,
	    SUBJECT, DESC % (instance.count, instance.product.name)
	)
		
