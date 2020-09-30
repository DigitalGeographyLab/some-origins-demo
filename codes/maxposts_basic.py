# -*- coding: utf-8 -*-
"""

Code associated to following manuscript:
    "Identifying the origins of social media users."

SOMEORIGINS - MAXPOSTS - BASIC

Script for identifying the most probable home country for Instagram users that have visited Kruger national park, SA.
The script calculates following things:
    - Exclude posts within target area (Kruger) from further analysis
    - For each user, calculate the country  with 1) most posts and 2) second most posts
    - Create an output file with probable home country, subregion and region for each user
    - Create an output file for regions, subregions and countries with number of home locations

Data:
     Input: Entire posting history of social media users who have visited the target area (visitors to Kruger national park in 2014)
     Input demo_data should already have information about the continent, sub-region and country of origin.

License:
    Creative Commons BY 4.0. See details from https://creativecommons.org/licenses/by/4.0/
"""

import geopandas as gpd
import pandas as pd
import os, sys
from fiona.crs import from_epsg


#-----------------------------------------------------------------------
# Functions used in this srcript
#-------------------------------------------------
def homelocation_maxposts(in_df, regioncolname, index=1):
    """Return the region with most posts (or 2nd most posts etc.) and associated photocount"""
    # Create index for accessing the correct position among potential homelocations
    i= index - 1

    # List number of posts per region:
    value_counts = in_df[regioncolname].value_counts()

    # get the region with most posts, 2nd mosts posts etc. depending on the index
    try:
        region, photo_cnt = value_counts.index[i], value_counts[value_counts.index[i]]

    except:
        region, photo_cnt = "N/A", 0

    # Return the region and associated photo count:
    return region, photo_cnt


def checkTop2homes(inDF, regioncol1, regioncol2):
    """ Check if the 1st and 2nd most probable home locations have the same amount of posts"""
    test = inDF[regioncol1] == inDF[regioncol2]
    print("Users with two candidates for home location:")
    print(test.value_counts())  #check output

    if len(test.value_counts())>1:
        print("check for conflict in", regioncol1, " & ", regioncol2, "!")

    else:
        print("No users with equal amount of posts in",regioncol1, " & ", regioncol2)


def aggregateRegionInfo(usershomelocations, region_column):
    """Return a dataframe with number of home locations per region"""
    homeRegionMatrix = pd.DataFrame()
    value_counts = usershomelocations[region_column].value_counts()

    # Iterate over values and produce DataFrame for country visitor numbers
    for region, cnt in zip(value_counts.index, value_counts.values):
        homeRegionMatrix = homeRegionMatrix.append([[region, cnt]])

    homeRegionMatrix.columns = [region_column, region_column + "_visitorcount"]

    return homeRegionMatrix


def joinHomeLocWithCountryShape(region_matrix, region_column, region_shape):
    """ join number of home locations per region with spatial demo_data"""
    region_join = region_shape.merge(region_matrix, how='outer', left_on= region_column, right_on = region_column + "1_basic")

    #Fill Nan
    region_join[region_column + "1_basic_visitorcount"] = region_join[region_column + "1_basic_visitorcount"].fillna(value=0)
    return region_join


# set method name
method_name = "basic_maxposts"

#--------------------------
# SOCIAL MEDIA DATA
#--------------------------
# Social media mobility history for Kruger national park visitors, with regioninfo, each point is assigned to the nearest region if found not on land
fp = r"./../demo_data/fake_input_data.shp"

#read demo_data with geopandas
some = gpd.read_file(fp)

# Print layer info
print("Number of posts:", len(some))
print("Number of users:", some.userid.nunique())

# EXCLUDE POSTS WITHIN KRUGER NATIONAL PARK (ASSUME NO ONE LIVES THERE..even though in fact people do live there..)
some = some[some["FromKruger"]==0]

# Print layer info
print("\nAfter excluding posts from Kruger:")
print("Number of posts:", len(some))
print("Number of users:", some.userid.nunique(), "\n")

# Group by individual users
grouped = some.groupby('userid')

#-----------------------------------------
# Detect 1st and 2nd country with maxposts for each user
#------------------------------------------

# Create GeoDataFrame for the results
geo = gpd.GeoDataFrame(crs=from_epsg(4326), columns = ['userid', 'post_cnt', "FIPS_1",
                                                       "FIPS_1_photocount", "FIPS_2", "FIPS_2_photocount"])

for userid, data in grouped:
    # Get userid and number of posts
    geo.loc[userid, "userid"] = userid
    geo.loc[userid, "post_cnt"] = len(data)

    # DETERMINE COUNTRY with 1st and 2nd most posts
    geo.loc[userid, ["FIPS_1", "FIPS_1_photocount"]] = homelocation_maxposts(data, "FIPS", 1)
    geo.loc[userid, ["FIPS_2", "FIPS_2_photocount"]] = homelocation_maxposts(data, "FIPS", 2)

# Check if there were any regions with equal amount of posts for some user
checkTop2homes(geo, "FIPS_1","FIPS_2")

# Initialize GeoDataFrame again
#geo = gpd.GeoDataFrame(geo, geometry='geometry', crs=from_epsg(4326))

# Reset index
geo = geo.reset_index(drop=True)

# save the user list with home country info in a file:
homelocs = geo

homelocs[method_name] = homelocs["FIPS_1"]


homelocs.to_csv(r"./../demo_results/%s_%susers.csv" % (method_name, str(homelocs.userid.nunique())),
                sep=";")

#------------------------------
# Aggregate results by region
#-----------------------------

# Calculate "home location" statistics for each regional unit
country_matrix = aggregateRegionInfo(geo, 'FIPS_1')
country_matrix.rename(columns={"FIPS_1_visitorcount": method_name},
                      inplace=True)

country_matrix.to_csv(r"./../demo_results/%s_%susers_by_country.csv" % (method_name, str(homelocs.userid.nunique())),
                      index = False,
                      sep=";")








