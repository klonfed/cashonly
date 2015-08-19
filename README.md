# CashOnly

Web-based cash system as a Django module. Supports LDAP for user authentication.

## Installation

### Dependencies
Use pip to install the Python packages from `requirements.txt`.

### Django setup
Start a new Django project:

`django-admin.py startproject <projectname>`

Copy the `cashonly` folder from this repo into the root folder of this project (next to `manage.py`).

#### Project settings
Open the file `<projectname>/settings.py` and add the following things:

Add `cashonly` and `bootstrapform` to the list of `INSTALLED_APPS`.

Add

`from django.conf import global_settings`

to the top of the file.

Add the line

`TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS + ('cashonly.views.version_number_context_processor',)`

Add the lines

```
LOGIN_URL = 'login/'
LOGIN_REDIRECT_URL = '/'
```

Add the line

`THUMBNAIL_SIZE = (150, 150)`

(adjust the values to your needs)

#### URL configuration
In order to provide the URLs from this module, add the following lines to `<projectname>/urls.py`:

```
url(r'', include('cashonly.urls')),

url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'cashonly/login.html'}),
url(r'^logout/$', 'django.contrib.auth.views.logout_then_login')
```

This will provide the cashonly URLs directly in the root of your project.

#### Database setup
Set the desired database options in `<projectname>/settings.py` and run

`python manage.py migrate`.

After that, you can create the first superuser with

`python manage.py createsuperuser`

#### Static files
Download bootstrap v3.0.0 (might work with newer versions too, but untested) from https://github.com/twbs/bootstrap/releases/tag/v3.0.0 and put the contents of the `dist` folder into `cashonly/static/bootstrap/`
Set the `STATIC_ROOT` and `STATIC_URL` according to https://docs.djangoproject.com/en/1.8/howto/static-files/ and run the `collectstatic` command.

#### Media files
Media files are required to be able to upload product images.
Set the `MEDIA_ROOT` and `MEDIA_URL` according to https://docs.djangoproject.com/en/1.8/topics/files/ .

### Deployment
See https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/ for instructions on how to deploy the project with a web server.
