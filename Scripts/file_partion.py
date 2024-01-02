import numpy as np
import pandas as pd

def partion(direction,links=[],count=3):
    df = pd.DataFrame(links)
    df.reset_index(drop=True, inplace=True)
    df["Node"] = df.index.map(lambda x: x % count + 1)
    df.to_csv(direction+"/Kategori.csv", index=False)
