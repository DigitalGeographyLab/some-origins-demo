"""
Code associated to following manuscript:
    "Identifying the origins of social media users."

Plot histogram of posts per user for Figure 1.
"""
import  geopandas as gpd
import seaborn as sns
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


# Plot histogram of posts per user
posts_per_user = some.groupby(by="userid").photoid.count()

#posts_per_user.plot.hist(bins=50)

ax = sns.distplot(posts_per_user, color="blue", kde=False)
#ax.set(xlabel='Posts per user outside KNP', ylabel='Posts per user', size=20)
ax.set_xlabel('Posts per user outside KNP', fontsize=20)
ax.set_ylabel('Number of users', fontsize=20)

plt.savefig(r"./demo_fig/userposthistogram.png")
plt.savefig(r"./demo_fig/userposthistogram.svg")
