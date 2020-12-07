import string
import spacy
import pytextrank
import pandas as pd

from math import sqrt
from pathlib import Path
from datetime import date, datetime


nlp = spacy.load('en_core_web_md') 

from spacytextblob.spacytextblob import SpacyTextBlob 
spacy_text_blob = SpacyTextBlob() 
nlp.add_pipe(spacy_text_blob) 

tr = pytextrank.TextRank()
nlp.add_pipe(tr.PipelineComponent, name="textrank", last=True)

df = pd.read_csv('emoji-faces.csv')

def make_spacy_doc(text):
    doc = nlp(text)
    return(doc)

# ----------- Generate relevant emoji through a simple sentiment-analysis grid
def sympathize(doc): 
    neutrality = 1 - doc._.sentiment.subjectivity
    return(doc._.sentiment.polarity, neutrality)

def hyp(coord, loc):
    a = abs(coord[0]-loc[0])
    b = abs(coord[1]-loc[1])
    c = sqrt(a**2 + b**2)
    return c

def emote(doc, memory, n=1):
    mem_text = " ".join(memory)[:-560] + doc.text
    mem_nopunc = mem_text.translate(str.maketrans('', '', string.punctuation))
    mem_doc = make_spacy_doc(mem_nopunc)
    coord = sympathize(mem_doc)
    distances = [(i, hyp(coord, (row["Sentiment score"], row["Neut"]))) for i, row in df.iterrows()]
    nearest = sorted(distances, key=lambda tup: tup[1])
    emojis = pd.DataFrame([(df["Char"][i], distance) for i, distance in nearest])
    return("".join([emoji for emoji in emojis[:n][0]]))

# ----------- Brainstorm new words from a given word
def translate(tok, from_word="simple", to_word="uncomplicated", n=10):
    tok_doc = make_spacy_doc(tok)
    if tok_doc.vector is None:
        return("something I don't know about")
    vec = tok_doc.vector - make_spacy_doc(from_word).vector #+ make_spacy_doc(to_word).vector
#     vec = tok_doc.vector
    vec_ids = nlp.vocab.vectors.most_similar(vec.reshape(1,vec.shape[0]), n=n)
    new_toks = [nlp.vocab.strings[vec] for i, vec in enumerate(vec_ids[0][0])]
    return(new_toks)

# ----------- Ask questions. This code seems unPythonic, need to fix that
def crappy_sort(doc, memory, n=5):
    if not doc._.phrases:
        return "..."
    thoughts = []
    for p in doc._.phrases: 
#         if p.text not in str(memory[:-500]).lower():
        for ent in doc.ents:
            if ent.text.lower() in p.text:
                if ent.label_ == "PERSON" or ent.label_ == "NORP" or ent.label_ == "ORG":
                    thoughts.append(f"Who is {ent.text}?")
                elif ent.label_ == "GPE" or ent.label_ == "FAC" or ent.label_ == "LOC": 
                    thoughts.append(f"Where is {ent.text}?")
                elif ent.label_ == "DATE" or ent.label_ == "TIME": 
                    thoughts.append(f"When is {ent.text}?")
                elif ent.label_ == "PERCENT" or ent.label_ == "MONEY"or ent.label_ == "QUANTITY": 
                    thoughts.append(f"How much is {ent.text}?")                
                else:
                    thoughts.append(f"What is {ent.text}? {ent.label_.capitalize()}?")
        new_toks = translate(p.text)
        if new_toks != []:
            thoughts.append(f"{p.text}...")
            for tok in new_toks:
                if tok.lower() not in str(memory).lower() and tok.lower() not in str(thoughts).lower():
                    thoughts.append(f"{tok}?...")
    return(" ".join(thoughts[:n]))

# ----------- For the interaction loop
def respond(stimulus, memory):
    doc = make_spacy_doc(stimulus)
    emoji = emote(doc, memory)
    query = crappy_sort(doc, memory, 5)
    return(f"\n\n----  {emoji} {query}\n\n")

# ----------- Link entities before writing to markdown
def tag_entities(doc):
    text = doc.text
    for e in doc.ents:
        if e.label_ not in ["CARDINAL", "ORDINAL", "MONEY", "QUANTITY", "PERCENT", "DATE"]:
            if str(e) in text:
                labeled_e = f"[[{str(e)}]]"
                if labeled_e not in text:
                    text = text.replace(str(e), labeled_e)
    return(text)

# ----------- Append markdown to day file with timestamp
def record(memory, outdir='output'):
    memory_doc = make_spacy_doc("".join(memory)) 
    memory_tagged = tag_entities(memory_doc)
    now = str(date.today()) + ".md"
    outpath = Path(outdir)/now
    with open(outpath, 'a') as f:
        print(f'## {datetime.now()}', file=f)
        print(memory_tagged, file=f)


# ----------- Interaction loop
print("\n\n----  😃 What's happening?\n\n")
stimulus = "Hi"
memory = []
while stimulus != "":
    stimulus = input()
    response = respond(stimulus, memory)
    memory.append(f'{stimulus}{response}')
    print(response)
record(memory)