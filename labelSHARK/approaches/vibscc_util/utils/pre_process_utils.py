from nltk import WordNetLemmatizer, word_tokenize, PorterStemmer
from nltk.corpus import wordnet
import re


def stemmer_tokenize(doc):
    lemmatizer = WordNetLemmatizer()
    terms = [lemmatizer.lemmatize(t,wordnet.VERB) for t in word_tokenize(doc)]
    return " ".join(terms)

class stemmer_tokenizer(object):
    def __init__(self):
        self.stemmer = PorterStemmer()

    def __call__(self, doc):
        return [self.stemmer.stem(t) for t in word_tokenize(doc)]


class stemmer_tokenizer_message(object):
    def __init__(self):
        self.stemmer = PorterStemmer()

    def __call__(self, doc):
        pattern = re.compile(r'-|/|\.|http|^[0-9]+$')
        wordsList = []
        for t in word_tokenize(doc):
            stem_word = self.stemmer.stem(t)
            if(pattern.search(stem_word) is None):
                wordsList.append(stem_word)
        return wordsList

