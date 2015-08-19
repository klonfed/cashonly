from django.conf.urls import patterns, url
from cashonly import views

urlpatterns = patterns('',
	url(r'^/?$', 'cashonly.views.overview', name='overview'),

	url(r'^product/(?P<pk>\d+)/$', views.ProductView.as_view(), name='product'),

	url(r'transactions/$', views.transactions, {'detailed': False, 'page':1}, name='transactions'),

	url(r'transactions/(?P<page>\d+)/$', views.transactions, {'detailed': False}, name='transactions'),

	url(r'transactions/(?P<page>\d+)/detailed/$', views.transactions, {'detailed': True},
	    name='transactions_detailed'),

	url(r'products/((?P<category_id>\d+)/)?$', views.products, name='products'),

	url(r'buy/(?P<product_id>\d+)/$', 'cashonly.views.buy', name='buy'),

	url(r'buy/(?P<product_id>\d+)/really/$', 'cashonly.views.buy',
	    {'confirm': True}, name='buy_really'),

	url(r'buy/thanks/$', 'cashonly.views.buy_thanks', name='buy_thanks'),

	url(r'buy/error/$', 'cashonly.views.buy_error', name='buy_error'),

	url(r'usersettings(/(?P<submit>\w+))?/$', 'cashonly.views.usersettings',
	    name='usersettings'),
)

