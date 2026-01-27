import numpy as np
import pandas as pd
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt


def prepare_samples(path):
    
    folder = Path(path)

    dfs = []

    for file in folder.glob("*.csv"):
        df = pd.read_csv(file)
        df["Vcc"] = file.name.replace(".csv", "")  # or file.stem if you want without .csv
        dfs.append(df)

    final_df = pd.concat(dfs, ignore_index=True)

    return final_df

if __name__ == "__main__":

    df = prepare_samples("./Measurement_results/")

    print(df)

    sns.scatterplot(data=df, x="pwr", y="I_avg [mA]", hue="Vcc")
    plt.grid(True)
    plt.show()