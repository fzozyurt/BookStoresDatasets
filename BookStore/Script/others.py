import numpy as np

def partion(links=[],count=5):
    part_links=np.array_split(links, count)
    print(part_links)
    return part_links

def export_csv(links=[],count=5):
    part_links=np.array_split(links, count)
    print(part_links)
    return part_links