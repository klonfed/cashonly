from django.views import generic
from django import forms
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.core import paginator
from cashonly.models import *
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy
import cashonly.version
import datetime

def version_number_context_processor(request):
	return {'version_number': cashonly.version.CASHONLY_VERSION}

@login_required
def overview(request):
	a = request.user.account
	time = datetime.datetime.now() - datetime.timedelta(hours=12)
	transactions = Transaction.objects.filter(account=a).filter(timestamp__gte=time).order_by('-timestamp')

	# FIXME: distinct doesn't work as expected, so fetch 20 rows and hope that there are 3 distinct products
	purchases = Product.objects.filter(saleslogentry__account=a).order_by('-saleslogentry__timestamp').distinct()[:20]

	products = []
	# Find 3 products
	for p in purchases:
		if not p in products:
			products.append(p)

		if len(products) == 3:
			break

	context = RequestContext(request, { 'latest_transactions': transactions,
	                                    'latest_purchases': products})

	return render_to_response('cashonly/index.html',
	                          context_instance=context)


class ProductView(generic.DetailView):
	model = Product


@login_required
def transactions(request, detailed, page):
	a = request.user.account
	transactions = Transaction.objects.filter(account=a).order_by('-timestamp')

	if page is None:
		page = 1

	pagi = paginator.Paginator(transactions, 10)
	try:
		transaction_list = pagi.page(page)
	except paginator.EmptyPage:
		transaction_list = paginator.page(paginator.num_pages)

	context = RequestContext(request, { 'transaction_list': transaction_list,
	                                    'detailed': detailed })

	return render_to_response('cashonly/transaction_list.html',
	                          context_instance=context)

def products(request, category_id=None):
	if category_id is None:
		category = None
		products = Product.objects.filter(active=True)
	else:
		category = get_object_or_404(ProductCategory, id=category_id)
		products = Product.objects.filter(active=True).filter(category=category)

	categories = ProductCategory.objects.all()

	context = RequestContext(request, { 'product_list': products,
	                                    'category': category,
	                                    'categories': categories })

	return render_to_response('cashonly/product_list.html',
	                          context_instance=context)

@login_required
def buy(request, product_id, confirm=False):
	product = get_object_or_404(Product, id=product_id)

	if confirm:
		if request.user.account.buy_product(product, 1):
			return redirect('buy_thanks')
		else:
			return redirect('buy_error')
	else:
		context = RequestContext(request, {'product': product})
		return render_to_response('cashonly/buy_confirm.html',
		                          context_instance=context)

@login_required
def buy_thanks(request):
	context = RequestContext(request)
	return render_to_response('cashonly/buy_thanks.html', context_instance=context)

@login_required
def buy_error(request):
	context = RequestContext(request)
	return render_to_response('cashonly/buy_error.html', context_instance=context)

class UserSettingsForm(forms.Form):
	daily_digest = forms.BooleanField(required=False,
	                                  label=ugettext_lazy('daily digest'))

class UserPinForm(forms.Form):
	pin = forms.CharField(max_length=32, widget=forms.PasswordInput,
	                      label=ugettext_lazy('PIN'), required=False)
	pin_confirm = forms.CharField(max_length=32, widget=forms.PasswordInput,
	                              label=ugettext_lazy('PIN (confirmation)'),
	                              required=False)

	def clean(self):
		cleaned_data = super(UserPinForm, self).clean()

		if not (cleaned_data.has_key('pin') or
		    cleaned_data.has_key('pin_confirm')):
			return cleaned_data
		if cleaned_data['pin'] != cleaned_data['pin_confirm']:
			raise forms.ValidationError(_('PINs do not match.'))

		return cleaned_data

@login_required
def usersettings(request, submit=None):
	daily_digest = request.user.account.daily_digest
	settings_form = UserSettingsForm({'daily_digest': daily_digest})
	pin_form = UserPinForm()

	if request.method == 'POST':
		if submit == 'pin':
			pin_form = UserPinForm(request.POST)

			if pin_form.is_valid():
				pin = pin_form.cleaned_data['pin']
				request.user.account.pin = pin
				request.user.account.save()
				context = RequestContext(request)
				return render_to_response('cashonly/usersettings_saved.html',
				                          context_instance=context)

		elif submit == 'settings':
			settings_form = UserSettingsForm(request.POST)

			if settings_form.is_valid():
				daily_digest = settings_form.cleaned_data['daily_digest']
				request.user.account.daily_digest = daily_digest
				request.user.account.save()
				context = RequestContext(request)
				return render_to_response('cashonly/usersettings_saved.html',
				                          context_instance=context)

	context = RequestContext(request, { 'settings_form': settings_form,
                                        'pin_form': pin_form})
	return render_to_response('cashonly/usersettings.html',
	                          context_instance=context)





