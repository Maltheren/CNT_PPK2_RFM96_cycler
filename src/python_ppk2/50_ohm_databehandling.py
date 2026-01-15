import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd





if __name__ == "__main__":

    man50 = pd.read_excel("TERM50_manual.ods")
    manant2 = pd.read_excel("ANT2_manual.ods")
    ppkant3 = pd.read_csv("ppk_antenna3.csv")
    manant3 = pd.read_excel("ant3_manual.ods")
    ppk50 = pd.read_csv("results_50.csv")
    plt.grid(True)
    sns.lineplot(data=ppk50, x="pwr", y="I_avg [mA]", errorbar=('sd', 2))
    sns.scatterplot(data=ppk50, x="pwr", y="I_avg [mA]", s=5, color='black')  # bigger red points


    sns.lineplot(data=man50, x="power", y="i_avg [mA]")
    sns.lineplot(data=manant2, x="power", y="i_avg [mA]")
    sns.lineplot(data=manant3, x="power", y="i_avg [mA]")

    sns.lineplot(data= ppkant3, x="pwr", y="I_avg [mA]",errorbar=('sd', 2))
    sns.scatterplot(data=ppkant3, x="pwr", y="I_avg [mA]", s=5, color='black')  # bigger red points


    plt.show()
