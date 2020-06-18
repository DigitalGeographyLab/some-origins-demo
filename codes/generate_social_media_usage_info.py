"""

Code associated to following manuscript:
    "Identifying the origins of social media users."


Generate social media usage info per user
"""
import pandas as pd
import  geopandas as gpd
import matplotlib.pyplot as plt
#--------------------------
# SOCIAL MEDIA DATA
#--------------------------

plt.style.use('grayscale')

# Social media mobility history for Kruger national park visitors, with regioninfo
#each point is assigned to the nearest region if found not on land. Also duplicates have been removed
fp = r"./demo_data/fake_input_data.shp"

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

# Prepare the demo_data
some["time_local"] = pd.to_datetime(some["time_local"])
# Separate months, weeks and days into own columns for cross-tabulation:
some["year"] = some.time_local.dt.to_period('Y')
some["month"] = some.time_local.dt.to_period('M')  # some["time_local"].apply(lambda x: x.month)
some["week"] = some.time_local.dt.to_period('W')
some["day"] = some.time_local.dt.to_period('D')

grouped = some.groupby("userid")

users = pd.DataFrame(index=some.userid.unique())

def posts_per_t(df, t):
    cf = df.groupby(t).photoid.nunique().std() / df.groupby(t).photoid.nunique().mean()
    return cf

for key, group in grouped:
    
    # Count of photos
    users.at[key, "photo_count"] = group.photoid.nunique()
    
    # Timedelta
    timedelta = group.time_local.max() - group.time_local.min()
    users.at[key, "timedelta"] = timedelta.days

    # Number of countries
    users.at[key, "country_count"] = group.FIPS.nunique()
    users.at[key, "posts_per_country_count_cf"] = posts_per_t(group, "FIPS")

    # Max time units
    users.at[key, "years"] = group.year.nunique()
    users.at[key, "months"] = group.month.nunique()
    users.at[key, "weeks"] = group.week.nunique()
    users.at[key, "days"] = group.day.nunique()
    
    # Coefficients of variation for posts per time unit
    users.at[key, "posts_per_year_cf"] = posts_per_t(group, "year")
    users.at[key, "posts_per_month_cf"] = posts_per_t(group, "month")
    users.at[key, "posts_per_week_cf"] = posts_per_t(group, "week")
    users.at[key, "posts_per_day_cf"] = posts_per_t(group, "day")


users.to_csv(r"./demo_data/fake_user_info.csv", index_label="userid", sep=";")