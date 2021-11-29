from math import sqrt
import pandas as pd

df = pd.read_csv('/home/farmer/farm/b3rduck/emoji-faces.csv')

# ----------- Generate relevant emoji through a simple sentiment-analysis grid
def sympathize(doc):
    neutrality = 1 - doc._.sentiment.subjectivity
    # The faces are generally lower in neutrality than other groups.
    # The maximum neutrality is "SMIRKING FACE" at 0.444, so normalize to that
    normed_neut = neutrality / 0.4444
    return(doc._.sentiment.polarity, normed_neut)

def hyp(coord, loc):
    a = abs(coord[0]-loc[0])
    b = abs(coord[1]-loc[1])
    c = sqrt(a**2 + b**2)
    return c

def emote(mem_doc, df, n=1):
    coord = sympathize(mem_doc)
    distances = [(i, hyp(coord, (row["Sentiment score"], row["Neut"]))) for i, row in df.iterrows()]
    nearest = sorted(distances, key=lambda tup: tup[1])
    emojis = pd.DataFrame([(df["Char"][i], distance) for i, distance in nearest])
    return("".join([emoji for emoji in emojis[:n][0]]))
