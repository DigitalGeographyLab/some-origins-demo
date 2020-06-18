# -*- coding: utf-8 -*-
"""

Code associated to following manuscript:
    "Identifying the origins of social media users."

SOMEORIGINS - TEMPORAL - HIERARCHICAL

Script for identifying the most probable home country for Instagram users that have visited Kruger national park, SA.
The script calculates following things:
    - MAXTIMEDELTA:
        - For each user, calculate
            a) the continent with longest time difference between first and last post
            b) within that continent, the subregion with longest time difference between first and last post
            c) within that region, the country with longest time difference between first and last post
        - Save results into csv (per user and per region)
    - MAX MONTH / WEEK / DAY
        - For each user, calculate
            a) the continent with maximum number of time units (months / weeks / days) with social media posts
            b) within that continent, calculate the region with maximum number of time units (months / weeks / days) with social media posts
            c) within that region, calculate the country with most time units (months / weeks / days) with social media posts
        - Save results into csv (month, week and day results per user and per region).

Data:
    Input: Mobility history of social media users who have visited a spesific area.
    Data is required to have region info in separate columns (generated with preprocess_somedata.py)

Created on:
    Mon May 26 2018

License:
    Creative Commons BY 4.0. See details from https://creativecommons.org/licenses/by/4.0/
"""

import geopandas as gpd
import pandas as pd
import random 
import os

def crosstabulate_users_posts_per_region(df, region_column):
    """Crosstabulate users posts per region"""
    post_count_matrix = pd.crosstab(df.userid, df[region_column])
    return post_count_matrix

def get_maxtimedelta_region(df, region_column):
    """ Calculate max time delta in each region for each user"""

    # Crosstabulate min and max timestamp for each user in each country (if they'be been there)
    crossTmin = pd.crosstab(df.userid, df[region_column], values=df.time_local, aggfunc=pd.Series.min)
    crossTmax = pd.crosstab(df.userid, df[region_column], values=df.time_local, aggfunc=pd.Series.max)

    # Calculate time difference for each user in each country. Returns a matrix of time deltas
    #NOTE: TAKING THE ABSOLUTE VALUE OF TIME DELTA
    timedelta_matrix = abs(crossTmin - crossTmax)

    # Get max time-difference and associated region
    timecol = "MAXTimeDeltas"

    timedelta_matrix[timecol] = timedelta_matrix.max(axis=1)
    #timedelta_matrix[regioncol] = timedelta_matrix.idxmax(axis=1)

    # Use another function to detect if user has posted equally as often from many countries, add related columns
    timedelta_matrix = list_maxtime_countries(df, timedelta_matrix, region_column, timecol="TimeDelta")

    # convert max time diff to format: days
    timedelta_matrix[timecol] = timedelta_matrix[timecol].apply(lambda x: x.days)

    return timedelta_matrix


def get_maxtime_region(df, region_column, timecol, truncate=True):
    """Cross-tabulate number of unique time units (days, months, weeks) in each country, and get country or
    list of countries where this value is highest into a new column"""

    # print("Crosstabulating number of unique %ss for each users within each region..." % timecol)
    time_matrix = pd.crosstab(df.userid, df[region_column], values=df[timecol], aggfunc=pd.Series.nunique)

    # Generate column names
    most_frequent_region = "%s_withMax%s" % (region_column, timecol)
    max_time_units = "MAX%ss" % timecol

    # Get max time-difference and associated region
    time_matrix[max_time_units] = time_matrix.max(axis=1)

    # NB! this would be wrong if multiple countries have the same number of time units!
    # time_matrix[most_frequent_region] = TimeMatrix_copy.idxmax(axis=1)

    if truncate:
        # take only info of the country with maximum posting frequency
        time_matrix = time_matrix[[most_frequent_region, max_time_units]]

    # Use another function to detect if user has posted equally as often from many countries, add related columns
    time_matrix = list_maxtime_countries(df, time_matrix, region_column, timecol)

    return time_matrix


def list_maxtime_countries(df, time_matrix, region_column, timecol):
    """Count how many countries have the max number of time units and
    List region codes of those regions which have equally many time units"""

    max_t_column = "MAX%ss" % (timecol)
    count_column = "N_of_%s_withMax%s" % (region_column, timecol)

    # Check how many potential values there are (how many columns in time matrix with country codes)
    datarange = df[region_column].nunique()

    #Count how many countries have the max number of time units
    for i, row, in time_matrix.iterrows():
        time_matrix.loc[i, count_column] = (row[:datarange] == row[max_t_column]).sum()

    #List Top Regions (check those instances where the number of time units equals to the max time unit) row by row.
    # (x.index is a series of the true values in each row!)
    # In other words; check the value range where country info is located using datarange,
    # and check which items are equal to the max time units
    time_matrix["HomeLocList"] = time_matrix.apply(lambda x: x.index[:datarange][x[:datarange] == x[max_t_column]].tolist(),
                                                   axis=1)

    return time_matrix


def get_regional_post_counts(user, countrylist, postcountDF):
    #Check how many countries this user has as candidates
    n_home_candidates = len(countrylist)

    #Dictionary for collecting candidates
    candidates = {}

    # Go trough countries, and find number of users for each country
    for listposition in range(n_home_candidates):
        # Populate the dictionary with region code and associated number of posts from this user
        candidates[countrylist[listposition]] = postcountDF.loc[user, countrylist[listposition]]
    return candidates


def apply_maxposts_to_candidate_countries(candidates):
    """In case the result contains two countries, this method check which of those countries have
    most posts based on a dictionary that contains the country code and post count. If there are several options
    after checking the number of posts, then the origin country is selected randomly among these.

    :param candidates: dictionary of users posts per country
    :return: Country with most posts
    """
    # Detect all items which have the maximum value
    home_loc = [key for key, value in candidates.items() if value == max(candidates.values())]

    if len(home_loc) == 1:
        return str(home_loc[0])
    else:
        # RANDOM COUNTRY OUT OF THE CANDIDATES (these countries have equal number of maxtime, and maxposts)
        return random.choice(home_loc)


def organize_output(time_matrix, postcountDF, result_column="home_loc_ok"):
    """Refine the homelocation resuts with number of posts per country"""
    time_matrix["userid"] = time_matrix.index
    time_matrix["homeLocDict"] = time_matrix.apply(lambda x: get_regional_post_counts(x["userid"],
                                                                                      x["HomeLocList"],
                                                                                      postcountDF),
                                                   axis=1)

    time_matrix[result_column] = time_matrix.apply(lambda x: apply_maxposts_to_candidate_countries(x["homeLocDict"]),
                                                   axis=1)

    return time_matrix

#-------------------------
# Result folder
#------------------------
folder = r"./demo_results"

#--------------------------
# SOCIAL MEDIA DATA
#--------------------------

# Social media mobility history for Kruger national park visitors, with regioninfo
# each point is assigned to the nearest region if found not on land. Also duplicates have been removed
fp = r"./demo_data/fake_input_data.shp"

#read demo_data with geopandas
some = gpd.read_file(fp)

# Print layer info
print("Number of posts:", len(some))
print("Number of users:", some.userid.nunique())

# Continue only with posts outside Kruger NP borders
some = some[some["FromKruger"] == 0]

# Print layer info
print("Number of posts without Kruger posts:", len(some))
print("Number of users without Kruger posts:", some.userid.nunique())

#convert time column to datetime format
some["time_local"] = pd.to_datetime(some["time_local"])

# Convert region codes to str
some[["RegCode", "SubReg_2"]] = some[["RegCode", "SubReg_2"]].astype(str) 

#-----------------------------------------------
# MAX TIME DIFFERENCE WITHIN REGION
#-----------------------------------------------

method_name = "hierarchical_maxtimedelta"

# REGION/CONTINENT with max time delta
maxtimedelta_continents = get_maxtimedelta_region(some, 'RegCode')

#Crosstabulate number of posts per REGCODE(needed if unambiquous result from temporal method)
users_posts_per_region = crosstabulate_users_posts_per_region(some, 'RegCode')

# Deal with unambiguous results:
maxtimedelta_continents = organize_output(maxtimedelta_continents, users_posts_per_region)

# Select columns for the next step (only needed info of user and RegCode
maxtimedelta_continents = maxtimedelta_continents[["userid", "home_loc_ok"]]

# SUB-REGION (in top continent)
#-------------------------------

# Subset original demo_data to top continents. Joining the demo_data drops out un-matching rows!
some_reg = some.merge(maxtimedelta_continents.reset_index(drop=True),
                      left_on=["userid", "RegCode"], right_on=["userid", 'home_loc_ok'])

# remove unnecessary column
some_reg.drop(columns="home_loc_ok", inplace=True)

# Crosstabulate number of posts per subgreg (needed if unambiguous result from temporal method)
users_posts_per_subregion = crosstabulate_users_posts_per_region(some_reg, 'SubReg_2')

# Calculate max time difference for each users subset pointa
maxtimedelta_subregion = get_maxtimedelta_region(some_reg, 'SubReg_2')

# Deal with unambiguous results:
maxtimedelta_subregion = organize_output(maxtimedelta_subregion, users_posts_per_subregion)

# Select columns for the next step (only needed info of user and RegCode
maxtimedelta_subregion = maxtimedelta_subregion[["userid", "home_loc_ok"]]

# COUNTRIES (in top subregion)
#------------------------------

# Subset original demo_data to top sub-regions. Joining the demo_data drops out un-matching rows!
some_subreg = some_reg.merge(maxtimedelta_subregion.reset_index(drop=True), left_on=["userid", 'SubReg_2'],
                             right_on=["userid", 'home_loc_ok'])
some_subreg.drop(columns="home_loc_ok", inplace=True)

# Crosstabulate number of posts per subgreg (needed if unambiquous result from temporal method)
users_posts_per_country = crosstabulate_users_posts_per_region(some_subreg, 'FIPS')

# Calculate max time difference for each users subset points
maxtimedelta_countries = get_maxtimedelta_region(some_subreg, 'FIPS')
    
# Deal with unambiguous results:
maxtimedelta_countries = organize_output(maxtimedelta_countries, users_posts_per_country, result_column=method_name)

# Write result to file by user
users_filename = "%s_%susers.csv" % (method_name, str(maxtimedelta_countries.index.nunique()))
maxtimedelta_countries.to_csv(os.path.join(folder, users_filename), sep=";")

# Write result to file by region
region_filename = "%s_%susers_by_country.csv" % (method_name, str(maxtimedelta_countries.index.nunique()))
maxtimedelta_countries[method_name].value_counts().to_csv(os.path.join(folder, region_filename),
                                                          sep=";",
                                                          index_label="FIPS",
                                                          header=[method_name])

# -----------------------------
# MAX MONTHS; WEEKS and DAYS
# -----------------------------

# Separate months, weeks and days into own columns for cross-tabulation:
some["month"] = some.time_local.dt.to_period('M') #some["time_local"].apply(lambda x: x.month)
some["week"] = some.time_local.dt.to_period('W')
some["day"] = some.time_local.dt.to_period('D')

for time in ["month", "week", "day"]:

    method_name = "hierarchical_max%ss" % time

    # CONTINENTS
    # -------------
    # Crosstabulate number of posts per REGCODE(needed if unambiquous result from temporal method)
    users_posts_per_region = crosstabulate_users_posts_per_region(some, 'RegCode')

    # Calculate continent with max days/weeks/months for each user
    maxtimes_continents = get_maxtime_region(some, 'RegCode', timecol=time, truncate=False)

    # Deal with unambiguous results:
    maxtimes_continents = organize_output(maxtimes_continents, users_posts_per_region)

    # Select columns for the next step (only needed info of user and RegCode
    maxtimes_continents = maxtimes_continents[["userid", "home_loc_ok"]]

    # SUB-REGIONS (in top continent)
    # -----------
    # Subset original demo_data to top continents. Joining the demo_data drops out un-matching rows!
    some_reg = some.merge(maxtimes_continents.reset_index(drop=True), left_on=["userid", "RegCode"],
                      right_on=["userid", 'home_loc_ok'])
    some_reg.drop(columns="home_loc_ok", inplace=True)

    # Crosstabulate number of posts per subgreg (needed if unambiguous result from temporal method)
    users_posts_per_subregion = crosstabulate_users_posts_per_region(some_reg, 'SubReg_2')

    # Calculate sub-region with max days/weeks/months for each user
    maxtimes_subregions = get_maxtime_region(some_reg, 'SubReg_2', timecol=time, truncate=False)

    # Deal with unambiguous results:
    maxtimes_subregions = organize_output(maxtimes_subregions, users_posts_per_subregion)

    # Select columns for the next step (only needed info of user and RegCode
    maxtimes_subregions = maxtimes_subregions[["userid", "home_loc_ok"]]

    # COUNTRIES (in top sub-region)
    # -----------------------------------

    # Subset original demo_data to top sub-regions. Joining the demo_data drops out un-matching rows!
    some_subreg = some_reg.merge(maxtimes_subregions.reset_index(drop=True), left_on=["userid", 'SubReg_2'],
                                 right_on=["userid", 'home_loc_ok'])
    some_subreg.drop(columns="home_loc_ok", inplace=True)

    # Crosstabulate number of posts per subgreg (needed if unambiquous result from temporal method)
    users_posts_per_country = crosstabulate_users_posts_per_region(some_subreg, 'FIPS')
    
    # Calculate country with max days/weeks/months for each user
    maxtimes_countries = get_maxtime_region(some_subreg, 'FIPS', timecol=time, truncate=False)

    # Deal with unambiguous results:
    maxtimes_countries = organize_output(maxtimes_countries, users_posts_per_country, result_column=method_name)

    # Write result to file by user
    users_filename = "%s_%susers.csv" % (method_name, str(maxtimes_countries.index.nunique()))
    maxtimes_countries.to_csv(os.path.join(folder, users_filename), sep=";")

    # Write result to file by region
    region_filename = "%s_%susers_by_country.csv" % (method_name, str(maxtimes_countries.index.nunique()))
    maxtimes_countries[method_name].value_counts().to_csv(os.path.join(folder, region_filename),
                                                              sep=";",
                                                              index_label="FIPS",
                                                              header=[method_name])
