import string
import spacy
import pytextrank
import numpy as np

from spacytextblob.spacytextblob import SpacyTextBlob
from pathlib import Path
from datetime import date, datetime

# from sense2vec import Sense2VecComponent

nlp = spacy.load('en_core_web_md')

#
# s2v = Sense2VecComponent(nlp.vocab).from_disk("/path/to/s2v_reddit_2015_md")
# nlp.add_pipe(s2v)

spacy_text_blob = SpacyTextBlob()
nlp.add_pipe(spacy_text_blob)

tr = pytextrank.TextRank()
nlp.add_pipe(tr.PipelineComponent, name="textrank", last=True)


# ------------ Cache the spacy function
# @st.cache(hash_funcs={spacy.tokens.doc.Doc : lambda doc: doc.text,   preshed.maps.PreshMap : lambda preshmap: preshmap.items(), spacy.vocab.Vocab: lambda voc : voc.strings})
def make_spacy_doc(text):
    doc = nlp(text)
    return(doc)

# Add vectors for emojis
vector_data = {}
with open('/home/farmer/farm/b3rduck/emoji2vec.txt', 'r') as f:
     for line in f:
        fields = line.split()
        word = fields[0]
        vector = np.fromiter((
        float(x) for x in fields[1:]), dtype=np.float32)
        vector_data[word] = vector

for word, vector in vector_data.items():
    nlp.vocab.set_vector(word, vector)
# ----------- Brainstorm new words from a given word

# Initialize the brainstormer.
from_word_doc = make_spacy_doc("simple")
to_word_doc = make_spacy_doc("uncomplicated")

# Linear algebra stuff
def shift_vec(from_doc_vector, to_doc_vector):
#         Maps an embedding unto another one.
    new_vec = ((from_doc_vector.dot(to_doc_vector))
        / (to_doc_vector.dot(to_doc_vector))
        * to_doc_vector)
    return(new_vec)

def bitwise_or(from_doc_vector, to_doc_vector):
#    Makes one embedding orthogonal to the other one.
    new_vec = from_doc_vector - (shift_vec(from_doc_vector, to_doc_vector))
    return(new_vec)

# @st.cache(hash_funcs={spacy.tokens.doc.Doc : lambda doc: doc.text,   preshed.maps.PreshMap : lambda preshmap: preshmap.items(), spacy.vocab.Vocab: lambda voc : voc.strings, spacy.strings.StringStore: lambda strin : len(strin)})
def translate(tok_doc, from_word_doc, to_word_doc, n=10):
    if tok_doc.vector is None:
        return("something I don't know about")
    vec = bitwise_or(tok_doc.vector, (from_word_doc.vector + to_word_doc.vector))
    # vec = tok_doc.vector
    vec_ids = nlp.vocab.vectors.most_similar(vec.reshape(1,vec.shape[0]), n=n)
    new_toks = [nlp.vocab.strings[vec] for i, vec in enumerate(vec_ids[0][0])]
    return(new_toks)

# ----------- Ask questions. This code seems unPythonic, need to fix that
# @st.cache(hash_funcs={spacy.tokens.doc.Doc : lambda doc: doc.text,   preshed.maps.PreshMap : lambda preshmap: preshmap.items(), spacy.vocab.Vocab: lambda voc : voc.strings})
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

        tok_doc = make_spacy_doc(p.text)
        new_toks = translate(tok_doc, from_word_doc, to_word_doc, 20)
        if new_toks != []:
            thoughts.append(f"{p.text}...")
            for tok in new_toks[6:]:
                if tok.lower() not in str(memory).lower() and tok.lower() not in str(thoughts).lower():
                    thoughts.append(f"{tok}?...")

    return(" ".join(thoughts[:n]))

# ----------- Link entities before writing to markdown
# @st.cache(hash_funcs={spacy.tokens.doc.Doc : lambda doc: doc.text,   preshed.maps.PreshMap : lambda preshmap: preshmap.items(), spacy.vocab.Vocab: lambda voc : voc.strings})
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
# @st.cache(hash_funcs={spacy.tokens.doc.Doc : lambda doc: doc.text,   preshed.maps.PreshMap : lambda preshmap: preshmap.items(), spacy.vocab.Vocab: lambda voc : voc.strings})
def record(doc, outdir='output'):
    memory_tagged = tag_entities(doc)
    now = str(date.today()) + ".md"
    outpath = Path(outdir)/now
    with open(outpath, 'a') as f:
        print(f'## {datetime.now()}', file=f)
        print(memory_tagged, file=f)
