from django.contrib import admin

from usda.models import Food, FoodGroup, Weight, Nutrient, Footnote, \
                        DataSource, DataDerivation, Source, NutrientData


class WeightAdmin(admin.ModelAdmin):
    raw_id_fields = ('food', )


class FootnoteAdmin(admin.ModelAdmin):
    raw_id_fields = ('food', )


class NutrientDataAdmin(admin.ModelAdmin):
    raw_id_fields = ('food', 'nutrient', )


admin.site.register(Food)
admin.site.register(FoodGroup)
admin.site.register(Weight, WeightAdmin)
admin.site.register(Nutrient)
admin.site.register(Footnote, FootnoteAdmin)
admin.site.register(DataSource)
admin.site.register(DataDerivation)
admin.site.register(Source)
admin.site.register(NutrientData, NutrientDataAdmin)