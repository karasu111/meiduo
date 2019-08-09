from django.conf.urls import url,include
from rest_framework_jwt.views import obtain_jwt_token
from meiduo_admin.views.home_views import *
from meiduo_admin.views.login_views import *
from meiduo_admin.views.user_views import UserAPIView
from meiduo_admin.views.sku_views import *
from rest_framework.routers import SimpleRouter
from . import views


urlpatterns = [
    #登录请求签发token
    url(r'^authorizations/$',obtain_jwt_token),
    # #用户总数
    # url(r'^statistical/total_count/$', HomeView.as_view({'get':'total_count'})),
    # #日新增用户
    # url(r'^statistical/day_increment/$', HomeView.as_view({'get': 'day_increment'})),
    # #日活跃用户
    # url(r'^statistical/day_active/$', HomeView.as_view({'get': 'day_active'})),

    url(r'^statistical/goods_day_views/$',GoodsVisitCountView.as_view()),

    url(r'^users/$',UserAPIView.as_view()),

    url(r'^skus/$',SKUViewSet.as_view({"get":"list", "post":"create"})),

    url(r'^skus/(?P<pk>\d+)/$',SKUViewSet.as_view({"get":"retrieve",
                                                   'put':'update',
                                                   'delete':'destroy'})),

    url(r'^skus/categories/$',SKUCategoryView.as_view()),

    url(r'^goods/simple/$', SPUSimpleView.as_view()),

    url(r'^goods/(?P<pk>\d+)/specs/$', SPUSpecView.as_view()),

]

router =SimpleRouter()
router.register(prefix='statistical',viewset=HomeView,base_name='home')
urlpatterns += router.urls