from django.db import models
from django.utils.translation import ugettext_lazy as _


FOOTNOTE_DESC = 'D'
FOOTNOTE_MEAS = 'M'
FOOTNOTE_NUTR = 'N'


FOOTNOTE_CHOICES=(
    (FOOTNOTE_DESC, _('Footnote adding information to the food  description')),
    (FOOTNOTE_MEAS, _('Footnote adding information to measure description')),
    (FOOTNOTE_NUTR, _('Footnote providing additional information on a nutrient value')),
)


class Food(models.Model):
    ndb_number = models.IntegerField(_('Nutrient Databank Number'), primary_key=True, help_text=_('Nutrient Databank number that uniquely identifies a food item.'))
    food_group = models.ForeignKey('FoodGroup', verbose_name=_('Food Group'), help_text=_('Food group to which a food item belongs.'))
    long_description = models.CharField(_('Long Description'), max_length=200, blank=True, help_text=_('Description of food item'))
    short_description = models.CharField(_('Short Description'), max_length=60, blank=True, help_text=_('Description of food item'))
    common_name = models.CharField(_('Common Name'), max_length=100, blank=True, help_text=_('Other names commonly used to describe a food, including local or regional names for various foods, for example, "soda" or "pop" for "carbonated beverages."'))
    manufacturer_name = models.CharField(_('Manufacturer Name'), max_length=65, blank=True, help_text=_('Indicates the company that manufactured the product, when appropriate.'))
    survey = models.BooleanField(_('Survey'), default=False, help_text=_('Indicates if the food item is used in the USDA Food and Nutrient Database for Dietary Studies (FNDDS) and thus has a complete nutrient profile for the 65 FNDDS nutrients.'))
    refuse_description = models.CharField(_('Refuse Description'), max_length=135, blank=True, help_text=_('Description of inedible parts of a food item (refuse), such as seeds or bone.'))
    refuse_percentage = models.IntegerField(_('Refuse Percentage'), blank=True, null=True, help_text=_('Percentage of refuse.'))
    scientific_name = models.CharField(_('Scientific Name'), max_length=65, blank=True, help_text=_('Scientific name of the food item. Given for the least processed form of the food (usually raw), if applicable.'))
    nitrogen_factor = models.FloatField(_('Nitrogen Factor'), blank=True, null=True, help_text=_('Factor for converting nitrogen to protein.'))    
    protein_factor = models.FloatField(_('Protein Factor'), blank=True, null=True, help_text=_('Factor for calculating calories from protein.'))
    fat_factor = models.FloatField(_('Fat Factor'), blank=True, null=True, help_text=_('Factor for calculating calories from fat.'))
    cho_factor = models.FloatField(_('CHO Factor'), blank=True, null=True, help_text=_('Factor for calculating calories from carbohydrate.'))

    class Meta:
        verbose_name = _('Food')
        verbose_name_plural = ('Foods')
        ordering = ['ndb_number']

    def __unicode__(self):
        return self.long_description

    @models.permalink
    def get_absolute_url(self):
        return ('usda-food_detail', (), { 'ndb_number': self.ndb_number })


class FoodGroup(models.Model):
    code = models.IntegerField(_('Food Group Code'), primary_key=True, help_text=_('Code identifying a food group. Codes may not be consecutive.'))
    description = models.CharField(_('Description'), max_length=60, blank=True, help_text=_('Name of food group.'))
    
    class Meta:
        verbose_name = _('Food Group')
        verbose_name_plural = _('Food Groups')
        ordering = ['code']

    def __unicode__(self):
        return self.description


class Nutrient(models.Model):
    number = models.IntegerField(_('Number'), primary_key=True, help_text=_('Unique identifier code for a nutrient.'))
    units = models.CharField(_('Units'), max_length=7, help_text=_('Units of measure (mg, g, and so on).'))
    tagname = models.CharField(_('Tagname'), max_length=20, blank=True, help_text=_('International Network of Food Data Systems (INFOODS) Tagnames. A unique abbreviation for a nutrient/food component developed by INFOODS to aid in the interchange of data.'))
    description = models.CharField(_('Description'), max_length=60, help_text=_('Name of nutrient/food component.'))
    decimals = models.IntegerField(_('Decimals'), help_text=_('Number of decimal places to which a nutrient value is rounded.'))
    order = models.IntegerField(_('Order'), help_text=_('Used to sort nutrient records in the same order as various reports produced from SR.'))

    class Meta:
        verbose_name = _('Nutrient')
        verbose_name_plural = _('Nutrients')
        ordering = ['number']
    
    def __unicode__(self):
        return self.description


class NutrientData(models.Model):
    food = models.ForeignKey('Food', verbose_name=_('Food'))
    nutrient = models.ForeignKey('Nutrient', verbose_name=_('Nutrient'))
    nutrient_value = models.FloatField(_('Nutrient Value'), help_text=_('Amount in 100 grams, edible portion.'))
    data_points = models.IntegerField(_('Data Points'), help_text=_('Number of data points (previously called Sample_Ct) is the number of analyses used to calculate the nutrient value. If the number of data points is 0, the value was calculated or imputed.'))
    standard_error = models.FloatField(_('Standard Error'), blank=True, null=True, help_text=_('Standard error of the mean. Null if can not be calculated.'))
    source = models.ManyToManyField('Source', verbose_name=_('Source'), help_text=_('Type of data'))
    data_derivation = models.ForeignKey('DataDerivation', verbose_name=_('Data Derivation'), blank=True, null=True, help_text=_('Data Derivation giving specific information on how the value is determined.'))
    reference_nbd_number = models.IntegerField(_('Reference NBD Number'), blank=True, null=True, help_text=_('NDB number of the item used to impute a missing value. Populated only for items added or updated starting with SR14.'))
    added_nutrient = models.BooleanField(_('Added Nutritient'), default=False, help_text=_('Indicates a vitamin or mineral added for fortification or enrichment. This field is populated for ready-to-eat breakfast cereals and many brand-name hot cereals in food group 8.'))
    number_of_studies = models.IntegerField(_('Number of Studies'), blank=True, null=True, help_text=_('Number of studies.'))
    minimum = models.FloatField(_('Minimum'), blank=True, null=True, help_text=_('Minimum value.'))
    maximum = models.FloatField(_('Maximum'), blank=True, null=True, help_text=_('Maximum value.'))
    degrees_of_freedom = models.IntegerField(_('Degrees of Freedom'), blank=True, null=True, help_text=_('Degrees of freedom.'))
    lower_error_bound = models.FloatField(_('Lower Error Bound.'), blank=True, null=True, help_text=_('Lower 95% error bound.'))
    upper_error_bound = models.FloatField(_('Upper Error Bound.'), blank=True, null=True, help_text=_('Upper 95% error bound.'))
    statistical_comments = models.CharField(_('Statistical Comments'), max_length=10, blank=True, help_text=_('Statistical comments.'))
    confidence_code = models.CharField(_('Confidence Code'), max_length=1, blank=True, help_text=_('Confidence Code indicating data quality, based on evaluation of sample plan, sample handling, analytical method, analytical quality control, and number of samples analyzed. Not included in this release, but is planned for future releases.'))

    class Meta:
        verbose_name = _('Nutrient Data')
        verbose_name_plural = _('Nutrient Data')
        ordering = ['food', 'nutrient']
        unique_together = ['food', 'nutrient']

    def __unicode__(self):
        return u'%s - %s' % (self.food, self.nutrient)


class Source(models.Model):
    code = models.IntegerField(_('Code'), primary_key=True)
    description = models.CharField(_('Description'), max_length=60, help_text=_('Description of source code that identifies the type of nutrient data.'))

    class Meta:
        verbose_name = _('Source')
        verbose_name_plural = _('Sources')
        ordering = ['code']

    def __unicode__(self):
        return self.description


class DataDerivation(models.Model):
    code = models.CharField(_('Code'), max_length=4, primary_key=True)
    description = models.CharField(_('Description'), max_length=120, help_text=_('Description of derivation code giving specific information on how the value was determined.'))

    class Meta:
        verbose_name = _('Data Derivation')
        verbose_name_plural = _('Data Derivations')
        ordering = ['code']

    def __unicode__(self):
        return self.description


class Weight(models.Model):
    food = models.ForeignKey('Food', verbose_name=_('Food'))
    sequence = models.IntegerField(_('Sequence'), help_text=_('Sequence number.'))
    amount = models.FloatField(_('Amount'), help_text=_('Unit modifier (for example, 1 in "1 cup").'))
    description = models.CharField(_('Description'), max_length=80, help_text=_('Description (for example, cup, diced, and 1-inch pieces).'))
    gram_weight = models.FloatField(_('Gram Weight'), help_text=_('Gram weight.'))
    number_of_data_points = models.FloatField(_('Number of Data Points'), blank=True, null=True, help_text=_('Number of data points.'))
    standard_deviation = models.FloatField(_('Standard Deviation'), blank=True, null=True, help_text=_('Standard Deviation'))

    class Meta:
        verbose_name = _('Weight')
        verbose_name_plural = _('Weights')
        ordering = ['food', 'sequence']
        unique_together = ['food' ,'sequence']

    def __unicode__(self):
        return u'%d %s %s %dg' % (self.amount, self.description, self.food, self.gram_weight)


class Footnote(models.Model):
    food = models.ForeignKey('Food', verbose_name=_('Food'))
    number = models.IntegerField(_('Sequence'), help_text=_('Sequence number. If a given footnote applies to more than one nutrient number, the same footnote number is used. As a result, this file cannot be indexed.'))
    type = models.CharField(_('Type'), max_length=1, choices=FOOTNOTE_CHOICES, help_text=_('Type of footnote.'))
    nutrient = models.ForeignKey('Nutrient', verbose_name=_('nutrient'), blank=True, null=True)
    text = models.CharField(_('Text'), max_length=200, help_text=_('Footnote text.'))
    
    class Meta:
        verbose_name = _('Footnote')
        verbose_name_plural = _('Footnotes')
        ordering = ['food', 'number']
        unique_together = ['food', 'number', 'nutrient']
    
    def __unicode__(self):
        return self.text


class DataSource(models.Model):
    id = models.CharField(_('Id'), max_length=6, primary_key=True, help_text=_('Unique number identifying the reference/source.'))
    authors = models.CharField(_('Authors'), max_length=255, blank=True, help_text=_('List of authors for a journal article or name of sponsoring organization for other documents.'))
    title = models.CharField(_('Title'), max_length=255, help_text=_('Title of article or name of document, such as a report from a company or trade association.'))
    year = models.IntegerField(_('Year'), blank=True, null=True, help_text=_('Year article or document was published.'))
    journal = models.CharField(_('Journal'), max_length=135, blank=True, null=True, help_text=_('Name of the journal in which the article was published.'))
    volume_or_city = models.CharField(_('Volume or City'), max_length=16, blank=True, help_text=_('Volume number for journal articles, books, or reports; city where sponsoring organization is located.'))
    issue_or_state = models.CharField(_('Issue or State'), max_length=5, blank=True, help_text=_('Issue number for journal article; State where the sponsoring organization is located.'))
    start_page = models.IntegerField(_('Start Page'), blank=True, null=True, help_text=_('Starting page number of article/document.'))
    end_page = models.IntegerField(_('End Page'), blank=True, null=True, help_text=_('Ending page number of article/document.'))

    class Meta:
        verbose_name = _('Data Source')
        verbose_name_plural = _('Data Sources')
        ordering = ['id']
    
    def __unicode__(self):
        return self.title
