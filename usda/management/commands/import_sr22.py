import csv
import decimal
import optparse
import logging
import os
import sys
import zipfile

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, DEFAULT_DB_ALIAS, reset_queries

from usda.models import Food, FoodGroup, Weight, Nutrient, Footnote, \
                        DataSource, DataDerivation, NutrientData, Source,\
                        FOOTNOTE_DESC, FOOTNOTE_MEAS, FOOTNOTE_NUTR


# Number of nutrient data items to read at once. Setting this too high may cause
# a MemoryException when `Debug=True` as query debugging information remains in RAM
NUTRIENT_DATA_STEP = 1000


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        optparse.make_option('-f', '--filename', action='store', dest='filename', help='The compressed SR22 filename', default='sr22.zip'),
        optparse.make_option('--database', action='store', dest='database', help='Specify database to load data into. Defaults to the "default" database.', default=DEFAULT_DB_ALIAS),
        optparse.make_option('--all', action='store_true', dest='all', help='Create/Update all data.'),
        optparse.make_option('--food', action='store_true', dest='food', help='Create/Update foods.'),
        optparse.make_option('--group', action='store_true', dest='group', help='Create/Update food groups.'),
        optparse.make_option('--nutrient', action='store_true', dest='nutrient', help='Create/Update nutrients.'),
        optparse.make_option('--weight', action='store_true', dest='weight', help='Create/Update weights.'),
        optparse.make_option('--footnote', action='store_true', dest='footnote', help='Create/Update footnotes.'),
        optparse.make_option('--datasource', action='store_true', dest='datasource', help='Create/Update data sources.'),
        optparse.make_option('--derivation', action='store_true', dest='derivation', help='Create/Update data derivations.'),
        optparse.make_option('--source', action='store_true', dest='source', help='Create/Update sources.'),
        optparse.make_option('--data', action='store_true', dest='data', help='Create/Update nutrient data.'),
    )
    help = 'Updates/Created all SR22 data.'
    
    def handle(self, **options):
        FOOD_DES = 'FOOD_DES.txt'
        FD_GROUP = 'FD_GROUP.txt'
        NUT_DATA = 'NUT_DATA.txt'
        NUTR_DEF = 'NUTR_DEF.txt'
        SRC_CD = 'SRC_CD.txt'
        DERIV_CD = 'DERIV_CD.txt'
        WEIGHT = 'WEIGHT.txt'
        FOOTNOTE = 'FOOTNOTE.txt'
        DATSRCLN = 'DATSRCLN.txt'
        DATA_SRC = 'DATA_SRC.txt'
        
        required_files = [
            FOOD_DES,
            FD_GROUP,
            NUT_DATA,
            NUTR_DEF,
            SRC_CD,
            DERIV_CD,
            WEIGHT,
            FOOTNOTE,
            DATSRCLN,
            DATA_SRC,
        ]
        
        verbosity = int(options.get('verbosity', 1))
        using = options.get('database', DEFAULT_DB_ALIAS)
        parse_all = options.get('all')
        parse_group = options.get('group')
        parse_food = options.get('food')
        parse_weight = options.get('weight')
        parse_nutrient = options.get('nutrient')
        parse_footnote = options.get('footnote')
        parse_datasource = options.get('datasource')
        parse_derivation = options.get('derivation')
        parse_source = options.get('source')
        parse_data = options.get('data')
        
        if not os.path.exists(options['filename']):
            CommandError('%s does not exist' % options['filename'])
        
        if verbosity == 1:
            logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
        elif verbosity > 1:
            logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')
        
        logging.info('Verifying %s...' % options['filename'])
        
        if not parse_all and not True in [
            parse_group, parse_food, parse_weight, parse_nutrient, parse_footnote,
            parse_datasource, parse_derivation, parse_source, parse_data
        ]:
            logging.info('Parsing all available data from %s' % options['filename'])
            parse_all = True
        
        zip_file = zipfile.ZipFile(options['filename'], mode='r')
        
        # Verify integrity of zip file by checking that all required files are present
        missing_files = [required_file for required_file in required_files if not required_file in zip_file.namelist()]
        if missing_files:
            logging.error('%s does not appear to be a valid SR22 database.  Unable to extract %s' % (filename, ', '.join(missing_files)))
        
        transaction.commit_unless_managed(using=using)
        transaction.enter_transaction_management(using=using)
        transaction.managed(True, using=using)
        
        if parse_all or parse_group:
            logging.info('Reading %s...' % FD_GROUP)
            create_update_food_groups(''.join([byte for byte in zip_file.read(FD_GROUP)]).splitlines())
        if parse_all or parse_food:
            logging.info('Reading %s...' % FOOD_DES)
            create_update_foods(''.join([byte for byte in zip_file.read(FOOD_DES)]).splitlines())
        if parse_all or parse_weight:
            logging.info('Reading %s...' % WEIGHT)
            create_update_weights(''.join([byte for byte in zip_file.read(WEIGHT)]).splitlines())
        if parse_all or parse_nutrient:
            logging.info('Reading %s...' % NUTR_DEF)
            create_update_nutrients(''.join([byte for byte in zip_file.read(NUTR_DEF)]).splitlines())
        if parse_all or parse_footnote:
            logging.info('Reading %s...' % FOOTNOTE)
            create_update_footnotes(''.join([byte for byte in zip_file.read(FOOTNOTE)]).splitlines())
        if parse_all or parse_datasource:
            logging.info('Reading %s...' % DATA_SRC)
            create_update_data_sources(''.join([byte for byte in zip_file.read(DATA_SRC)]).splitlines())
        if parse_all or parse_derivation:
            logging.info('Reading %s...' % DERIV_CD)
            create_update_derivations(''.join([byte for byte in zip_file.read(DERIV_CD)]).splitlines())
        if parse_all or parse_source:
            logging.info('Reading %s...' % SRC_CD)
            create_update_sources(''.join([byte for byte in zip_file.read(SRC_CD)]).splitlines())
        if parse_all or parse_data:
            logging.info('Reading %s...' % NUT_DATA)
            create_update_nutrient_data(''.join([byte for byte in zip_file.read(NUT_DATA)]).splitlines())
        
        transaction.commit(using=using)
        transaction.leave_transaction_management(using=using)
        
        zip_file.close()


def create_update_food_groups(data):
    total_created = 0
    total_updated = 0
    
    logging.info('Processing %d food groups' % len(data))
    
    for row in csv.DictReader(
        data, fieldnames=('fdgrp_cd', 'fdgrp_desc'),
        delimiter='^', quotechar='~'
    ):
        created = False
        
        try:
            food_group = FoodGroup.objects.get(code=int(row['fdgrp_cd']))
            total_updated += 1
        except FoodGroup.DoesNotExist:
            food_group = FoodGroup(code=int(row['fdgrp_cd']))
            total_created += 1
            created = True
        
        food_group.description = row['fdgrp_desc']
        food_group.save()
        
        if created:
            logging.debug('Created %s' % food_group)
        else:
            logging.debug('Updated %s' % food_group)
    
    logging.info('Created %d new food groups' % total_created)
    logging.info('Updated %d food groups' % total_updated)


def create_update_foods(data):
    total_created = 0
    total_updated = 0
    
    logging.info('Processing %d foods' % len(data))
    
    for row in csv.DictReader(
        data,
        fieldnames=(
            'ndb_no', 'fdgrp_cd', 'long_desc', 'short_desc', 'com_name',
            'manufac_name', 'survey', 'ref_desc', 'refuse', 'sci_name',
            'n_factor', 'pro_factor', 'fat_factor', 'cho_factor'
        ),
        delimiter='^', quotechar='~'
    ):
        created = False
        
        try:
            food = Food.objects.get(ndb_number=int(row['ndb_no']))
            total_updated += 1
        except Food.DoesNotExist:
            food = Food(ndb_number=int(row['ndb_no']))
            total_created += 1
            created = True
        
        food.food_group = FoodGroup.objects.get(code=int(row['fdgrp_cd']))
        food.long_description = row.get('long_desc')
        food.short_description = row.get('short_desc')
        food.common_name = row.get('com_name')
        food.manufacturer_name = row.get('manufac_name')
        if row.get('survey'):
            food.survey = row['survey'] == 'Y'
        food.refuse_description = row.get('ref_desc')
        if row.get('refuse'):
            food.refuse_precentage = int(row['refuse'])
        if row.get('sci_name'):
            food.scientific_name = row['sci_name']
        if row.get('n_factor'):
            food.nitrogen_factor = float(row['n_factor'])
        if row.get('pro_factor'):
            food.protein_factor = float(row['pro_factor'])
        if row.get('fat_factor'):
            food.fat_factor = float(row['fat_factor'])
        if row.get('cho_factor'):
            food.cho_factor = float(row['cho_factor'])
        
        food.save()
        
        if created:
            logging.debug('Created %s' % food)
        else:
            logging.debug('Updated %s' % food)
    
    logging.info('Created %d new foods' % total_created)
    logging.info('Updated %d foods' % total_updated)


def create_update_weights(data):
    total_created = 0
    total_updated = 0
    
    logging.info('Processing %d weights' % len(data))
    
    for row in csv.DictReader(
        data, fieldnames=(
            'ndb_no', 'seq', 'amount', 'msre_desc', 'gm_wgt', 'num_data_pts', 'std_dev'
        ),
        delimiter='^', quotechar='~'
    ):
        created = False
        
        try:
            weight = Weight.objects.get(
                food=Food.objects.get(ndb_number=int(row['ndb_no'])),
                sequence=int(row['seq'])
            )
            total_updated += 1
        except Weight.DoesNotExist:
            weight = Weight(
                food=Food.objects.get(ndb_number=int(row['ndb_no'])),
                sequence=int(row['seq'])
            )
            total_created += 1
            created = True
        
        weight.amount = float(row.get('amount'))
        weight.description = row.get('msre_desc')
        weight.gram_weight = float(row.get('gm_wgt'))
        if row.get('num_data_pts'):
            weight.number_of_data_points = float(row['num_data_pts'])
        if row.get('std_dev'):
            weight.standard_deviation = float(row['std_dev'])
        weight.save()
        
        if created:
            logging.debug('Created %s' % weight)
        else:
            logging.debug('Updated %s' % weight)
    
    logging.info('Created %d new weights' % total_created)
    logging.info('Updated %d weights' % total_updated)


def create_update_nutrients(data):
    total_created = 0
    total_updated = 0
    
    logging.info('Processing %d nutrients' % len(data))
    
    for row in csv.DictReader(
        data, fieldnames=(
            'nutr_no', 'units', 'tagname', 'nutrdesc', 'num_dec', 'sr_order'
        ),
        delimiter='^', quotechar='~'
    ):
        created = False
        
        try:
            nutrient = Nutrient.objects.get(number=int(row['nutr_no']))
            total_updated += 1
        except Nutrient.DoesNotExist:
            nutrient = Nutrient(number=int(row['nutr_no']))
            total_created += 1
            created = True
        
        nutrient.units = row['units']
        nutrient.tagname = row.get('tagname')
        nutrient.description = row['nutrdesc']
        nutrient.decimals = int(row['num_dec'])
        nutrient.order = int(row['sr_order'])
        nutrient.save()
        
        if created:
            logging.debug('Created %s' % nutrient)
        else:
            logging.debug('Updated %s' % nutrient)
    
    logging.info('Created %d new nutrients' % total_created)
    logging.info('Updated %d nutrients' % total_updated)


def create_update_footnotes(data):
    total_created = 0
    total_updated = 0
    
    logging.info('Processing %d footnotes' % len(data))
    
    for row in csv.DictReader(
        data, fieldnames=(
            'ndb_no', 'footnt_no', 'footnt_typ', 'nutr_no', 'footnt_txt'
        ),
        delimiter='^', quotechar='~'
    ):
        created = False
        
        # SR22 definition indicates that `footnt_no` and `footnt_typ` are required,
        # but on occasion, either on is blank.  To compensate for this, we assume
        # a blank `footnt_no` is '1' and a blank`footnt_typ` is 'N'.
        if row['footnt_no'] == '':
            row['footnt_no'] = 1
        if row['footnt_typ'] not in (FOOTNOTE_DESC, FOOTNOTE_MEAS, FOOTNOTE_NUTR):
            row['footnt_typ'] = FOOTNOTE_NUTR
        
        if row.get('nutr_no'):
            nutrient = Nutrient.objects.get(number=int(row['nutr_no']))
        else:
            nutrient = None
        
        try:
            footnote = Footnote.objects.get(
                food=Food.objects.get(ndb_number=int(row['ndb_no'])),
                number=int(row['footnt_no']),
                nutrient=nutrient
            )
            total_updated += 1
        except Footnote.DoesNotExist:
            footnote = Footnote(
                food=Food.objects.get(ndb_number=int(row['ndb_no'])),
                number=int(row['footnt_no']),
                nutrient=nutrient
            )
            total_created += 1
            created = True
        
        footnote.type = row['footnt_typ']
        footnote.text = row['footnt_txt']
        footnote.save()
        
        if created:
            logging.debug('Created %s' % footnote)
        else:
            logging.debug('Updated %s' % footnote)
    
    logging.info('Created %d new footnotes' % total_created)
    logging.info('Updated %d footnotes' % total_updated)


def create_update_data_sources(data):
    total_created = 0
    total_updated = 0
    
    logging.info('Processing %d data sources' % len(data))
    
    for row in csv.DictReader(
        data, fieldnames=(
            'datasrc_id', 'authors', 'title', 'year', 'journal',
            'vol_city', 'issue_state', 'start_page', 'end_page'
        ),
        delimiter='^', quotechar='~'
    ):
        created = False
        
        try:
            data_source = DataSource.objects.get(id=row['datasrc_id'])
            total_updated += 1
        except DataSource.DoesNotExist:
            data_source = DataSource(id=row['datasrc_id'])
            total_created += 1
            created = True
        
        data_source.description = row.get('authors')
        data_source.title = row.get('title')
        if row.get('year'):
            data_source.year = int(row['year'])
        data_source.journal = row.get('journal')
        data_source.volume_or_city = row.get('vol_city')
        data_source.issue_or_state = row.get('issue_state')
        if row.get('start_page'):
            data_source.start_page = row.get('start_page')
        if row.get('end_page'):
            data_source.end_page = row.get('end_page')
        data_source.save()
        
        if created:
            logging.debug('Created %s' % data_source)
        else:
            logging.debug('Updated %s' % data_source)
    
    logging.info('Created %d new data sources' % total_created)
    logging.info('Updated %d data sources' % total_updated)


def create_update_derivations(data):
    total_created = 0
    total_updated = 0
    
    logging.info('Processing %d data derivations' % len(data))
    
    for row in csv.DictReader(
        data, fieldnames=('deriv_cd', 'deriv_desc'),
        delimiter='^', quotechar='~'
    ):
        created = False
        
        try:
            derivation = DataDerivation.objects.get(code=row['deriv_cd'])
            total_updated += 1
        except DataDerivation.DoesNotExist:
            derivation = DataDerivation(code=row['deriv_cd'])
            total_created += 1
            created = True
        
        # SR22 defines `deriv_desc` as being a maximum length of 120 characters,
        # however, there is at least one instance where `deriv_desc` is greater
        # than this max.  To deal with this, truncate to 120 characters.
        derivation.description = row['deriv_desc'][:120]
        derivation.save()
        
        if created:
            logging.debug('Created %s' % derivation)
        else:
            logging.debug('Updated %s' % derivation)
    
    logging.info('Created %d new derivations' % total_created)
    logging.info('Updated %d derivations' % total_updated)


def create_update_sources(data):
    total_created = 0
    total_updated = 0
    
    logging.info('Processing %d sources' % len(data))
    
    for row in csv.DictReader(
        data, fieldnames=('src_cd', 'srccd_desc'),
        delimiter='^', quotechar='~'
    ):
        created = False
        
        try:
            source = Source.objects.get(code=int(row['src_cd']))
            total_updated += 1
        except Source.DoesNotExist:
            source = Source(code=int(row['src_cd']))
            total_created += 1
            created = True
        
        source.description = row['srccd_desc']
        source.save()
        
        if created:
            logging.debug('Created %s' % source)
        else:
            logging.debug('Updated %s' % source)
    
    logging.info('Created %d new sources' % total_created)
    logging.info('Updated %d sources' % total_updated)


def create_update_nutrient_data(data):
    total_created = 0
    total_updated = 0
    
    logging.info('Processing %d nutrient data items' % len(data))

    for start in range(0, len(data), NUTRIENT_DATA_STEP):
        end = min(start + NUTRIENT_DATA_STEP, len(data))
        
        for row in csv.DictReader(
            data[start:end], fieldnames=(
                'ndb_no', 'nutr_no', 'nutr_val', 'num_data_pts', 'std_error',
                'src_cd', 'deriv_cd', 'ref_ndb_no', 'add_nutr_mark', 'num_studies',
                'min', 'max', 'df', 'low_eb', 'up_eb', 'stat_cmt', 'cc'
            ),
            delimiter='^', quotechar='~'
        ):
            created = False
        
            try:
                nutrient_data = NutrientData.objects.get(
                    food=Food.objects.get(ndb_number=int(row['ndb_no'])),
                    nutrient=Nutrient.objects.get(number=int(row['nutr_no']))
                )
                total_updated += 1
            except NutrientData.DoesNotExist:
                nutrient_data = NutrientData(
                    food=Food.objects.get(ndb_number=int(row['ndb_no'])),
                    nutrient=Nutrient.objects.get(number=int(row['nutr_no']))
                )
                total_created += 1
                created = True
        
            nutrient_data.nutrient_value = float(row['nutr_val'])
            nutrient_data.data_points = int(row['num_data_pts'])
            if row.get('std_error'):
                nutrient_data.standard_error = float(row['std_error'])
            if row.get('deriv_cd'):
                nutrient_data.data_derivation = DataDerivation.objects.get(code=row['deriv_cd'])
            if row.get('ref_ndb_no'):
                nutrient_data.reference_nbd_number = int(row['ref_ndb_no'])
            if row.get('add_nutr_mark'):
                nutrient_data.added_nutrient = row['add_nutr_mark'] == 'Y'
            if row.get('num_studies'):
                nutrient_data.number_of_studies = int(row['num_studies'])
            if row.get('min'):
                nutrient_data.minimum = float(row['min'])
            if row.get('max'):
                nutrient_data.maximum = float(row['max'])
            if row.get('df'):
                nutrient_data.degrees_of_freedom = int(row['df'])
            if row.get('low_eb'):
                nutrient_data.lower_error_bound = float(row['low_eb'])
            if row.get('up_eb'):
                nutrient_data.upper_error_bound = float(row['up_eb'])
            nutrient_data.statistical_comments = row.get('stat_cmt')
            nutrient_data.confidence_code = row.get('cc')
            nutrient_data.save()
        
            if row.get('src_cd'):
                nutrient_data.source.add(Source.objects.get(code=row['src_cd']))
                nutrient_data.save()
        
            if created:
                logging.debug('Created %s' % nutrient_data)
            else:
                logging.debug('Updated %s' % nutrient_data)
                
        reset_queries() # Reset DB connection to avoid using all available RAM
    
    logging.info('Created %d new nutrient data' % total_created)
    logging.info('Updated %d nutrient data' % total_updated)
