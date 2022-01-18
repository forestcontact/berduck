import spacy
import pytextrank
import numpy as np
import importlib.resources as pkg_resources

from spacytextblob.spacytextblob import SpacyTextBlob

nlp = spacy.load('en_core_web_md')
nlp.add_pipe('spacytextblob')
nlp.add_pipe('textrank')

# Add vectors for emojis
vector_data = {}
emoji_vectors = pkg_resources.open_text(__package__, 'emoji2vec.txt')
for line in emoji_vectors:
    fields = line.split()
    word = fields[0]
    vector = np.fromiter((float(x) for x in fields[1:]), dtype=np.float32)
    vector_data[word] = vector

for word, vector in vector_data.items():
    nlp.vocab.set_vector(word, vector)

def make_spacy_doc(text):
    doc = nlp(text)
    return(doc)

# ----------- Brainstorm new words from a given word

# Initialize the brainstormer.
from_word_doc = make_spacy_doc("complicated")
to_word_doc = make_spacy_doc("simple")

# Linear algebra stuff
def shift_vec(from_doc_vector, to_doc_vector):
#   Maps an embedding unto another one.
    new_vec = ((from_doc_vector.dot(to_doc_vector))
        / (to_doc_vector.dot(to_doc_vector))
        * to_doc_vector)
        
    return(new_vec)

def bitwise_or(from_doc_vector, to_doc_vector):
#    Makes one embedding orthogonal to the other one.
    new_vec = from_doc_vector - (shift_vec(from_doc_vector, to_doc_vector))
    return(new_vec)

def translate(tok_doc, from_word_doc, to_word_doc, n=10):
    if tok_doc.vector is None:
        return("something I don't know about")

    vec = bitwise_or(tok_doc.vector, (from_word_doc.vector + to_word_doc.vector))
    vec_ids = nlp.vocab.vectors.most_similar(vec.reshape(1,vec.shape[0]), n=n)
    new_toks = [nlp.vocab.strings[vec] for i, vec in enumerate(vec_ids[0][0])]
    return(new_toks)


# ----------- Ask questions. This code seems unPythonic, need to fix that
def crappy_sort(doc, memory='', n=5):
    if not doc._.phrases:
        return "..."

    thoughts = []
    for p in doc._.phrases:
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

        tok_doc = make_spacy_doc(p.text)
        new_toks = translate(tok_doc, from_word_doc, to_word_doc, 20)
        
        if new_toks != []:
            thoughts.append(f"{p.text}...")          
            for tok in new_toks[6:]:
                if tok.lower() not in str(memory).lower() and tok.lower() not in str(thoughts).lower():
                    thoughts.append(f"{tok}?...")

    return(" ".join(thoughts[:n]))

# ----------- Grab emoji sentiments from file
import csv
from math import sqrt

emoji_faces = pkg_resources.open_text(__package__, 'emoji-faces.csv')
emoji_reader = csv.reader(emoji_faces)
emoji_list = [row[:3] for row in emoji_reader][1:]

# ----------- Generate relevant emoji through a simple sentiment-analysis grid
def sympathize(doc):
    neutrality = 1 - doc._.subjectivity
    # The faces are generally lower in neutrality than other groups.
    # The maximum neutrality is "SMIRKING FACE" at 0.444, so normalize to that
    normed_neut = neutrality / 0.4444
    return(doc._.polarity, normed_neut)

def hyp(coord, loc):
    a = abs(coord[0]-loc[0])
    b = abs(coord[1]-loc[1])
    c = sqrt(a**2 + b**2)
    return c

def emote(mem_doc, n=1):
    coords = sympathize(make_spacy_doc(mem_doc))

    distances = []
    for i, row in enumerate(emoji_list):
        face, neutrality, polarity = row
        loc = hyp(coords, (float(polarity), float(neutrality)))
        distances.append((i, loc))

    nearest = sorted(distances, key=lambda tup: tup[1])

    emojis = [(emoji_list[i][0], distance) for i, distance in nearest]
    return("".join([emoji[0] for emoji in emojis[:n]]))

# ----------- For the interaction loop
def respond(stimulus, memory=''):
    stim_doc = make_spacy_doc(stimulus)
    emoji = emote(stim_doc)
    query = crappy_sort(stim_doc, memory, 5)
    return(f"{emoji} {query}")