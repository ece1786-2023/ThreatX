# -*- coding: utf-8 -*-
"""baseline.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/131UO5iPwm9KuSQhczBIYLSaDp5x7DaHa
"""

!pip install -U spacy

!python -m spacy download en_core_web_sm

import json


train_file = "data.json"

def load_data(data_path=train_file):
  with open(train_file, 'r') as json_file:
      data = json.load(json_file)
  return data

def extract_entities(annotation):
    start = annotation['start']
    end = annotation['end']
    label = annotation['label'].upper()
    return start, end, label

def process_example(example):
    entities = [extract_entities(annotation) for annotation in example['annotations']]
    return {
        'text': example['text'],
        'entities': entities
    }

data = load_data()
training_data = [process_example(example) for example in data]

import random
def split_data_train_dev(data):
  indices = list(range(len(data)))
  train_idx = random.sample(indices, 25)
  training_data = [data[i] for i in train_idx]
  test_idx = [i for i in indices if i not in train_idx]
  testing_data = [data[j] for j in test_idx]

  return training_data, testing_data

def process_training_example(nlp, training_example):
    text = training_example['text']
    labels = training_example['entities']
    doc = nlp.make_doc(text)
    entities = []

    for start, end, label in labels:
        span = doc.char_span(start, end, label=label, alignment_mode="contract")
        if span is None:
          span1 = doc.char_span(start, end+1, label=label, alignment_mode="contract")
          if span1 is None:
            print(f"Skipping invalid entity: {label} [{start}:{end}]")
          else:
            entities.append(span1)
        else:
            entities.append(span)

    filtered_entities = spacy.util.filter_spans(entities)
    doc.ents = filtered_entities
    return doc

import spacy
from spacy.tokens import DocBin
from tqdm import tqdm

def convert_to_spacy(training_data, output_path, desc="Processing training data"):
  # Load a new spaCy model
  nlp = spacy.blank("en")
  # Create a DocBin to store processed documents
  doc_bin = DocBin()
  # Process training data and add to DocBin
  for training_example in tqdm(training_data, desc=desc):
      processed_doc = process_training_example(nlp, training_example)
      doc_bin.add(processed_doc)

  # Save the processed documents to disk
  doc_bin.to_disk(output_path)

len(training_data)

train, test = split_data_train_dev(training_data)
convert_to_spacy(train, "train.spacy")
convert_to_spacy(test, "dev.spacy", "Processing testing data")

#initialize config
!python -m spacy init fill-config base_config.cfg base_config.cfg

#train
!python -m spacy train base_config.cfg --output ./output --paths.train /content/train.spacy --paths.dev /content/dev.spacy

nlp_ner = spacy.load("./output/model-best")
colors = {"IP": "#F08080", "MALWARE_NAME": "#EEE8AA", "DOMAIN_NAME":"#8FBC8B",
          "HASH_VAL":"#F9E79F", "ACTOR": "#F7DC6F", "HASH_VAL":"#F4D03F",
          "REG_KEY": "#FAD7A0", "GEO_LOCATION":"#F8C471", "URL": "#F5B041"}
options = {"colors": colors}

for example in test:
  doc = nlp_ner(example.get('text'))
  print("....Next batch .....")
  spacy.displacy.render(doc, style="ent", options= options, jupyter=True)

# Commented out IPython magic to ensure Python compatibility.
# %load_ext autoreload
# %autoreload 2
from IPython.lib.pretty import PrettyPrinter
import spacy
from spacy.scorer import Scorer
from spacy.training.example import Example

def evaluate(nlp_ner, test_data):
  scorer = Scorer()
  example = []
  for obs in test_data:
    # print('Input for a prediction:', obs['text'])
    pred = nlp_ner(obs['text'])  ## custom_nlp is the custome model I am using to generate docs
    # print('Predicted based off of input:', pred, '// Entities being reviewed:', obs['entities'])
    temp = Example.from_dict(pred, {'entities': obs['entities']})
    example.append(temp)
  scores = scorer.score_spans(example, "ents")
  return scores

# example run
results = evaluate(nlp_ner, test)

results