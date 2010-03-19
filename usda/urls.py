from django.conf.urls.defaults import *


urlpatterns = patterns('usda.views',
    url(r'^$', 'food_list', name='usda-food_list'),
    url(r'^(?P<ndb_number>\d+)/$', 'food_detail', name='usda-food_detail'),
)
