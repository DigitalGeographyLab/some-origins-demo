
"""
Code associated to following manuscript:
    "Identifying the origins of social media users."

Plot graph for supplementary materials
"""

import os
import pandas as pd
import glob
import matplotlib.pyplot as plt

plt.style.use('seaborn-whitegrid')

# Results by user
in_folder = r"./demo_results/cluster_options"
files = glob.glob(os.path.join(in_folder,"matches*csv"))

data = pd.read_csv(files[0])
data.set_index("km", drop=True, inplace=True)

for csv in files[1:]:
    ref = pd.read_csv(csv)
    ref.set_index("km", drop=True, inplace=True)
    data = data.join(ref)

data = data[['hierarchical_RegCode',
            'hierarchical_SubReg_2',
              'hierarchical_FIPS',
              'basic_FIPS']]

data.sort_index().plot(style=['^-','^-','^-', 's-'], fontsize=14)


plt.legend(["Continent - Hierarchical",
            "Sub-region - Hierarchical",
            "Country - Hierarchical",
            "Country - Basic"], fontsize=16)

plt.gca().set_yticklabels(['{:.0f}%'.format(x*100) for x in plt.gca().get_yticks()])

plt.ylabel("Match with expert assessment", fontsize=16)
plt.xlabel('Epsilon (km)', fontsize=16)

plt.xticks([1, 10, 25, 60, 120, 210, 340, 500, 725, 1000], [1, "", "", 60, 120, 210, 340, 500, 725, 1000], fontsize=12)

plt.show()