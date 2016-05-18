from django.conf.urls import url
import views

urlpatterns = [
    url(r'^auth',                    views.auth),
    url(r'^$',                      views.index),
]
