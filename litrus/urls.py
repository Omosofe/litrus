from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin


urlpatterns = [
	url(r'^accounts/', include('litrus.modules.accounts.urls', namespace='accounts')),
	url(r'^courses/', include('litrus.modules.courses.urls', namespace='courses')),
	url(r'^', include('litrus.modules.pages.urls', namespace='pages')),
	url(r'^payments/paypal/', include('paypal.standard.ipn.urls')),
    url(r'^admin/', include(admin.site.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
