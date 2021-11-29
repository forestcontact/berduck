""" Utility and hashing functions """

def hash_spacy_doc(doc):
    return doc.text

def hash_spacy_vocab(vocab):
    return vocab.strings

def hash_spacy_map(preshmap):
    return preshmap.items()
