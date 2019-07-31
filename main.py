# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.4'
#       jupytext_version: 1.1.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# # National Insurance number allocations to adult overseas nationals to March 2018
#
# Convert spreadsheet from
#
# https://www.gov.uk/government/statistics/national-insurance-number-allocations-to-adult-overseas-nationals-to-march-2018
#
# Table 1: NINo registrations to adult overseas nationals entering the UK by quarter of registration and world region

from gssutils import *
scraper = Scraper('https://www.gov.uk/government/statistics/' \
                  'national-insurance-number-allocations-to-adult-overseas-nationals-to-march-2018')
scraper

sheets = scraper.distribution(
    title='Summary tables: National Insurance number allocations to adult overseas nationals to March 2018',
    mediaType=ODS
).as_databaker()
[t.name for t in sheets]

# The tab/sheet named '1' has "Table 1: NINo registrations to adult overseas nationals entering the UK by quarter of registration and world region"

savepreviewhtml(sheets[1])

observations = sheets[1].excel_ref('B8').expand(DOWN).expand(RIGHT).is_not_blank()
area = sheets[1].excel_ref('B6').expand(RIGHT).is_not_blank()
period = sheets[1].excel_ref('A8').expand(DOWN).is_not_blank()
period = period - period.regex('^INFO').expand(DOWN)
dimensions = [
    HDim(period,'Period',DIRECTLY,LEFT),
    HDim(area,'Nationality', DIRECTLY, ABOVE),
    HDimConst('Measure Type', 'Count'),
    HDimConst('Unit','People')
]
cs = ConversionSegment(observations, dimensions, processTIMEUNIT=True)
savepreviewhtml(cs)

table1 = cs.topandas()
table1.head()

table1['Value'] = table1['OBS'].astype(int)
table1 = table1[['Period','Nationality','Measure Type','Value','Unit']].copy()
table1.head()

# Periods are "British Calendar" quarters, so convert e.g. `Jan-02 to Mar-02` to `quarter/2002-Q1`

# +
import re
quarter_re = re.compile('\*?(Jan|Apr|Jul|Oct)-([0-9]{2}) to (Mar|Jun|Sep|Dec)-([0-9]{2})')
def to_quarter(s):
    match = quarter_re.match(s)
    assert match, f"period {s} doesn't match pattern"
    assert match.group(2) == match.group(4), "quarter start and end must be in the same year"
    if match.group(1) == 'Jan':
        assert match.group(3) == 'Mar', 'Quarter starting in Jan should end in Mar'
        return f"quarter/20{match.group(2)}-Q1"
    elif match.group(1) == 'Apr':
        assert match.group(3) == 'Jun', 'Quarter starting in Apr should end in Jun'
        return f"quarter/20{match.group(2)}-Q2"
    elif match.group(1) == 'Jul':
        assert match.group(3) == 'Sep', 'Quarter starting in Jul should end in Sep'
        return f"quarter/20{match.group(2)}-Q3"
    elif match.group(1) == 'Oct':
        assert match.group(3) == 'Dec', 'Quarter starting in Oct should end in Dec'
        return f"quarter/20{match.group(2)}-Q4"

table1['Period'] = table1['Period'].map(to_quarter)
# -

# Table 2: Adult overseas nationals entering the UK by Region / Local Authority and world region

savepreviewhtml(sheets[2])

# +
observations = sheets[2].excel_ref('C9').expand(DOWN).expand(RIGHT).is_not_blank() - sheets[2].excel_ref('A432').expand(RIGHT)
area = sheets[2].excel_ref('C5').expand(RIGHT).is_not_blank()
RLa = sheets[2].excel_ref('A9').expand(DOWN).is_not_blank()

Dimensions = [
            HDim(RLa,'Geography',DIRECTLY,LEFT),
            HDim(area,'Nationality', DIRECTLY, ABOVE),
            HDimConst('Measure Type', 'Count'),
            HDimConst('Unit','People')
            ]
cs = ConversionSegment(observations, Dimensions, processTIMEUNIT=True)
savepreviewhtml(cs)
# -

table2 = cs.topandas()
table2.head()

# Drop non-numeric observations and ignore data markers.
#
# Todo: figure out how to represent missing measured values.

import numpy as np
table2['OBS'].replace('', np.nan, inplace=True)
table2.dropna(subset=['OBS'], inplace=True)
table2.rename(columns={'OBS': 'Value'}, inplace=True)
table2['Value'] = table2['Value'].astype(int)
table2.drop(columns=['DATAMARKER'], inplace=True)
table2.head()

# Table 3: NIN to adult Overseas Nationals Entering The UK by World region and nationality

savepreviewhtml(sheets[3])

observations = sheets[3].excel_ref('C29:D29').expand(DOWN).is_not_blank()
citizenship = sheets[3].excel_ref('B29').expand(DOWN).is_not_blank()
period = sheets[3].excel_ref('C3:D3')
period = period - period.regex('^INFO').expand(DOWN)
Dimensions = [
            HDim(period,'Period',DIRECTLY,ABOVE),
            HDim(citizenship,'Nationality', DIRECTLY, LEFT),
            HDimConst('Measure Type', 'Count'),
            HDimConst('Unit','People')
            ]
cs = ConversionSegment(observations, Dimensions, processTIMEUNIT=True)
savepreviewhtml(cs)

table3 = cs.topandas()
table3.head()

# Drop non-numeric observations and ignore data markers.
#
# Todo: figure out how to represent missing measured values.

import numpy as np
table3['OBS'].replace('', np.nan, inplace=True)
table3.dropna(subset=['OBS'], inplace=True)
table3.rename(columns={'OBS': 'Value'}, inplace=True)
table3['Value'] = table3['Value'].astype(int)
table3.drop(columns=['DATAMARKER'], inplace=True)
table3 = table3[['Period','Nationality','Measure Type','Value','Unit']]
table3.head()

# Convert periods to what look to be "Government years", see https://github.com/epimorphics/IntervalServer/blob/master/interval-uris.md#modern-government-business-intervals
#     

year_to_re = re.compile('^Yr to March ([0-9]{4})$')
def to_govyear(s):
    match = year_to_re.match(s)
    assert match, f"Period '{s}' doesn't match pattern"
    y = match.group(1)
    return f'government-year/{int(y)-1}-{y}'
table3['Period'] = table3['Period'].map(to_govyear)
table3.head()

# Consider each table as a slice with hidden constant dimension:
#
# * `table1` needs `Geography` to be the UK, or `K02000001`
# * `table2` needs `Period` to be year to March 2018, or `government-year/2017-2018`
# * `table3` needs `Geography` to be the UK, or `K02000001`

table1['Geography'] = 'K02000001'
table2['Period'] = 'government-year/2017-2018'
table3['Geography'] = 'K02000001'
full_table = pd.concat([table1, table2, table3], sort=False)
full_table.head()

# Derive the nationalities and groupings from the final tab of the spreadsheet

world_regions = sheets[4].filter('World region').fill(DOWN).is_not_blank()
sub_groups = world_regions.shift(RIGHT)
nationalities = sub_groups.shift(RIGHT)
savepreviewhtml([world_regions, sub_groups, nationalities])

# +
regions = set(r.value for r in world_regions)
sub_group_parents = {}
for group in sub_groups:
    parent = group.shift(LEFT).value
    if group.value in sub_group_parents:
        assert sub_group_parents[group.value] == parent, 'sub group in multiple regions'
    else:
        sub_group_parents[group.value] = parent
nationality_parents = {}
for nationality in nationalities:
    parent = nationality.shift(LEFT).value
    if nationality.value in nationality_parents:
        assert nationality_parents[nationality.value] == parent, 'nationality in multiple sub groups'
    else:
        nationality_parents[nationality.value] = parent

codelist = [
    ('All nationalities', 'all', '')
] + [
    (region, pathify(region), 'all')
    for region in regions
] + [
    (sub_group, pathify(sub_group), pathify(parent))
    for sub_group, parent in sub_group_parents.items()
] + [
    (nationality, pathify(nationality), pathify(parent))
    for nationality, parent in nationality_parents.items()
] + [
    ('Unknown', 'unknown', 'all')   
]

codelist_df = pd.DataFrame.from_records(codelist, columns=('Label', 'Notation', 'Parent Notation'))
codelist_df['Sort Priority'] = codelist_df.index + 1
codelist_df['Description'] = ''
if not codelist_df['Notation'].is_unique:
    display(codelist_df[codelist_df.duplicated('Notation', keep='first')])
    assert False, "Notation not unique for nationalities codelist"
out = Path('out')
out.mkdir(exist_ok=True)
codelist_df.to_csv(out / 'nationalities.csv', index=False)


# -

# Use codes for nationality and check they exist in the above codelist

# +
def notation(s):
    r = pathify(s)
    if r == 'total':
        return 'all'
    elif r == 'other-/-unknown':
        return 'unknown'
    elif r == 'st-helena-ascension-and-tristan-da-cunha':
        return 'st-helena'
    return r

full_table['Nationality'] = full_table['Nationality'].apply(notation)
used_nationalities = set(full_table['Nationality'].unique())
declared_nationalities = set(codelist_df['Notation'].unique())
assert used_nationalities.issubset(declared_nationalities), used_nationalities - declared_nationalities
# -

# One issue is that table 2 has for the last row 'Overseas registration'. For now, we'll split the output into two tables so that we can use two different definitions of the same component/dimension.

ons_geo_table = full_table[full_table['Geography'].notnull()]
overseas_table = full_table[~full_table['Geography'].notnull()].copy()
overseas_table['Registration Geography'] = 'Overseas'
overseas_table.drop(columns=['Geography'], inplace=True)

# +
from pathlib import Path
destinationFolder = Path('out')
destinationFolder.mkdir(exist_ok=True, parents=True)

ons_geo_table.to_csv(destinationFolder / ('observations.csv'), index = False)
overseas_table.to_csv(destinationFolder / ('overseas_observations.csv'), index = False)

# +
from gssutils.metadata import THEME
scraper.dataset.family = 'migration'
scraper.dataset.theme = THEME['population']

with open(destinationFolder / 'dataset.trig', 'wb') as metadata:
    metadata.write(scraper.generate_trig())
# -
csvw = CSVWMetadata('https://ons-opendata.github.io/ref_migration/')
csvw.create(out / 'observations.csv', out / 'observations.csv-schema.json')



