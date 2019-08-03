from django.conf.urls import url
from . import views
from rest_framework_jwt.views import obtain_jwt_token

urlpatterns = [
    url(r'^register/$',views.RegisterView.as_view()),
    #用户名是否重复
    url(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$', views.UsernameCountView.as_view()),
    # 手机号是否重复
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),
    url(r'^login/$',views.LoginView.as_view()),
    url(r'^logout/$',views.LogoutView.as_view()),
    url(r'^info/$',views.InfoView.as_view()),
    url(r'^emails/$',views.EmailView.as_view()),
    url(r'^emails/verification/$',views.VerifyEmailView.as_view()),
    url(r'^addresses/$',views.AddressView.as_view()),
    url(r'^addresses/create/$',views.CreateAddressView.as_view()),
    url(r'^addresses/(?P<address_id>\d+)/$',views.UpdateDestroyAddressView.as_view()),
    url(r'^addresses/(?P<address_id>\d+)/default/$',views.DefaultAddressView.as_view()),
    url(r'^addresses/(?P<address_id>\d+)/title/$',views.UpdateTitleAddressView.as_view()),
    url(r'^password/$', views.ChangePasswordView.as_view()),
    url(r'^browse_histories/$', views.HistoryGoodsView.as_view()),
    url(r'^orders/info/(?P<page_num>\d+)/$',views.OrdersInfoView.as_view()),
    url(r'^find_password/$',views.ForgetPasswordView.as_view()),
    url(r'^accounts/(?P<username>\w+)/sms/token/$',views.InputCountView.as_view()),
    url(r'^sms_codes/$',views.VerifyUsernameView.as_view()),
    url(r'^authorizations/$', obtain_jwt_token),

]