from django.conf.urls import url
from . import views


urlpatterns = [
    # url(r'^areas/$',views.AreasView.as_view()),
    url(r'^areas/$', views.AreaView.as_view()),
]



