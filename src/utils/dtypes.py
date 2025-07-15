from typing import Literal


TYPE_CODETYPES = Literal[
    'ASHRAE901',
    'ASHRAE1891',
    'IECC'
]


prototypes = [
    "RestaurantSitDown",
    "RetailStandalone",
    "RetailStripMall",
    "SchoolPrimary",
    "SchoolSecondary",
    "Warehouse",
    "ApartmentHighRise",
    "ApartmentMidRise",
    "Hospital",
    "HotelLarge",
    "HotelSmall",
    "OfficeLarge",
    "OfficeMedium",
    "OfficeSmall",
    "OutPatientHealthCare",
    "RestaurantFastFood",
]


prototype_numbers = {
    'ApartmentHighRise': '01',
    'ApartmentMidRise': '02',
    'Hospital': '03',
    'HotelSmall': '04',
    'HotelLarge': '05',
    'OfficeMedium': '06',
    'OfficeLarge': '07',
    'OfficeSmall': '08',
    'OutPatientHealthCare': '09',
    'RestaurantFastFood': '10',
    'RestaurantSitDown': '11',
    'RetailStandalone': '12',
    'RetailStripmall': '13',
    'SchoolPrimary': '14',
    'SchoolSecondary': '15',
    'Warehouse': '16',
}

TYPE_PROTOTYPES = Literal[
    "RestaurantSitDown",
    "RetailStandalone",
    "RetailStripMall",
    "SchoolPrimary",
    "SchoolSecondary",
    "Warehouse",
    "ApartmentHighRise",
    "ApartmentMidRise",
    "Hospital",
    "HotelLarge",
    "HotelSmall",
    "OfficeLarge",
    "OfficeMedium",
    "OfficeSmall",
    "OutPatientHealthCare",
    "RestaurantFastFood"
]


TYPE_STD_YEAR = Literal[
    "STD2004",
    "STD2007",
    "STD2010",
    "STD2013",
    "STD2016",
    "STD2019",
    "STD2022",
    "STD2025"
]







TYPE_CITY_NAME = Literal[
    "Albuquerque",
    "Atlanta",
    "Buffalo",
    "Denver",
    "Dubai",
    "ElPaso",
    "Fairbanks",
    "GreatFalls",
    "HoChiMinh",
    "InternationalFalls",
    "Miami",
    "NewDelhi",
    "NewYork",
    "PortAngeles",
    "Rochester",
    "SanDiego",
    "Seattle",
    "Tampa",
    "Tucson"
]


TYPE_CZ = Literal[
    "4B",
    "3A",
    "5A",
    "5B",
    "0B",
    "3B",
    "8",
    "6B",
    "0A",
    "7",
    "1A",
    "1B",
    "4A",
    "5C",
    "6A",
    "3C",
    "4C",
    "2A",
    "2B"
]


TYPE_WEATHER_FILES = Literal[
    "USA_NM_ALBUQUERQUE",
    "USA_GA_ATLANTA",
    "USA_NY_BUFFALO",
    "USA_CO_DENVER",
    "ARE_DUBAI_DUBAIINTL",
    "USA_TX_ELPASO",
    "USA_AK_FAIRBANKS",
    "USA_MT_GREATFALLS",
    "VNM_HOCHIMINH_TANSONHOA",
    "USA_MN_INTERNATIONALFALLS",
    "USA_FL_MIAMI",
    "IND_DELHI_NEWDELHI",
    "USA_NY_NEWYORK",
    "USA_WA_PORTANGELES",
    "USA_MN_ROCHESTER",
    "USA_CA_SANDIEGO",
    "USA_WA_SEATTLE",
    "USA_FL_TAMPA",
    "USA_AZ_TUCSON"
]


SIM_METHODOLOGY = Literal['prismm-measure', 'prototype']


# state-code specific entries


TYPE_STD_YEAR_STATECODE = Literal[
    'STD2004',
    'STD2007',
    'STD2010',
    'STD2013',
    'STD2016',
    'STD2019',
    'STD2022',
    'STD2021',
    'STD2006',
    'STD2009',
    'STD2012',
    'STD2015',
    'STD2018'
]





TYPE_STATE_STATECODE = Literal[
    'DC', 'GA', 'MD', 'MI', 'MN', 'NC', 'NY', 'RI', 'VT', 'WI', 'AK',
    'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DE', 'FL', 'HI', 'IA', 'ID',
    'IL', 'IN', 'KS', 'KY', 'LA', 'MA', 'ME', 'MO', 'MS', 'MT', 'ND',
    'NE', 'NH', 'NJ', 'NM', 'NV', 'OH', 'OK', 'OR', 'PA', 'SC', 'SD',
    'TN', 'TX', 'UT', 'VA', 'WA', 'WV', 'WY'
]


TYPE_CITY_STATECODE = Literal[
    'DC-BALTIMORE-MD', 'GA-ATLANTA-GA', 'GA-SAVANNAH-GA',
    'MD-BALTIMORE-MD', 'MD-PITTSBURGH-PA', 'MI-ALPENACOUNTY-MI',
    'MI-LANSING-MI', 'MI-SAULTSTEMARIE-MI', 'MN-DULUTH-MN',
    'MN-MINNEAPOLISSTPAUL-MN', 'MN-WINONA-MN', 'NC-ASHEVILLE-NC',
    'NC-CHARLOTTE-NC', 'NC-ELKINS-WV', 'NY-ALBANY-NY', 'NY-MASSENA-NY',
    'NY-NEWYORK-NY', 'RI-PROVIDENCE-RI', 'VT-BURLINGTON-VT',
    'WI-GREENBAY-WI', 'WI-MILWAUKEE-WI', 'AK-ANCHORAGE-AK',
    'AK-FAIRBANKS-AK', 'AK-JUNEAU-AK', 'AK-KETCHIKAN-AK',
    'AL-BIRMINGHAM-AL', 'AL-MOBILE-AL', 'AR-FAYETTEVILLE-AR',
    'AR-LITTLEROCK-AR', 'AZ-GALLUP-NM', 'AZ-KINGMAN-AZ',
    'AZ-PRESCOTT-AZ', 'AZ-TUCSON-AZ', 'CA-ARCATA-CA', 'CA-BISHOP-CA',
    'CA-EAGLECOUNTY-CO', 'CA-LOSANGELES-CA', 'CA-SANFRANCISCO-CA',
    'CA-TUCSON-AZ', 'CA-WINNERMUCCA-NV', 'CO-COLORADOSPRINGS-CO',
    'CO-EAGLECOUNTY-CO', 'CO-GUNNISONCOUNTY-CO', 'CO-TRINIDAD-CO',
    'CT-HARTFORDBRADLEY-CT', 'DE-WILMINGTON-DE', 'FL-MIAMI-FL',
    'FL-TAMPA-FL', 'HI-HONOLULU-HI', 'IA-DESMOINES-IA',
    'IA-MASONCITY-IA', 'ID-BOISE-ID', 'ID-IDAHOFALLS-ID',
    'IL-PEORIA-IL', 'IL-STLOUIS-MO', 'IN-EVANSVILLE-IN',
    'IN-FORTWAYNE-IN', 'KS-GOODLAND-KS', 'KS-TOPEKA-KS',
    'KY-LEXINGTON-KY', 'LA-BATONROUGE-LA', 'LA-SHREVEPORT-LA',
    'MA-BOSTONLOGAN-MA', 'ME-BANGOR-ME', 'ME-CARIBOU-ME',
    'MO-KIRKSVILLE-MO', 'MO-MEMPHIS-TN', 'MO-STLOUIS-MO',
    'MS-JACKSON-MS', 'MS-MOBILE-AL', 'MT-HELENA-MT', 'ND-BISMARCK-ND',
    'ND-MINOT-ND', 'NE-OMAHA-NE', 'NH-LEBANON-NH', 'NH-MANCHESTER-NH',
    'NJ-ALLENTOWN-PA', 'NJ-NEWARK-NJ', 'NM-ALBUQUERQUE-NM',
    'NM-GALLUP-NM', 'NM-ROSWELL-NM', 'NV-LASVEGAS-NV', 'NV-TONOPAH-NV',
    'NV-WINNERMUCCA-NV', 'OH-CLEVELAND-OH', 'OH-COLUMBUS-OH',
    'OK-AMARILLO-TX', 'OK-OKLAHOMA-OK', 'OK-PONCACITY-OK',
    'OR-PORTLAND-OR', 'OR-REDMOND-OR', 'PA-PHILADELPHIA-PA',
    'PA-PITTSBURGH-PA', 'SC-BEAUFORT-SC', 'SC-COLUMBIA-SC',
    'SD-SIOUXCITY-IA', 'SD-SIOUXFALLS-SD', 'TN-BRISTOL-TN',
    'TN-MEMPHIS-TN', 'TX-AMARILLO-TX', 'TX-BROWNSVILLE-TX',
    'TX-ELPASO-TX', 'TX-HOUSTON-TX', 'TX-LAREDO-TX',
    'TX-WICHITAFALLS-TX', 'UT-SAINTGEORGE-UT', 'UT-SALTLAKECITY-UT',
    'UT-VERNAL-UT', 'VA-ELKINS-WV', 'VA-NORFOLK-VA', 'VA-RICHMOND-VA',
    'WA-KALISPELL-MT', 'WA-QUILLAYUTE-WA', 'WA-SEATTLE-WA',
    'WA-SPOKANE-WA', 'WV-CHARLESTON-WV', 'WV-ELKINS-WV',
    'WY-CASPER-WY', 'WY-CHEYENNE-WY', 'WY-JACKSONHOLE-WY'
]


TYPE_ANALYSIS_PURPOSE_STATECODE = Literal[
    'STATECODE.BASELINE',
    'STATECODE.CURRENT'
]
