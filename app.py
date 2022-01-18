from pathlib import Path
from datetime import date, datetime
from berduck.core import make_spacy_doc, respond

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

if __name__ == "__main__":
    print("\n\n----  😃 What's happening?\n\n")
    stimulus = "Hi"
    memory = []
    while stimulus != "exit":
        stimulus = input()
        response = respond(stimulus, memory)
        memory.append(f'{stimulus}{response}')
        print(f'\n\n----  {response}\n\n')
    # record(memory)