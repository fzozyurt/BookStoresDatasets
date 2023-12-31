import numpy as np

def filepartion(direction,links=[],count=3):
    part_links=np.array_split(links, count)
    print(part_links)
    i=0
    while i<count:
        with open(direction+'/links-'+str(i)+'.txt', 'w') as f:
            for line in part_links[i]:
                f.write(f"{line}\n")
        f.close()
        i=i+1