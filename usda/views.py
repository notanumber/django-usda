from django.views.generic import list_detail

from usda.models import Food


def food_list(request, template_name='usda/food_list.html'):
    return list_detail.object_list(
        request, Food.objects.all(),
        template_name=template_name,
        template_object_name='food',
    )


def food_detail(request, ndb_number, template_name='usda/food_detail.html'):
    return list_detail.object_detail(
        request, Food.objects.all(),
        object_id=ndb_number,
        template_name=template_name,
        template_object_name='food',
    )