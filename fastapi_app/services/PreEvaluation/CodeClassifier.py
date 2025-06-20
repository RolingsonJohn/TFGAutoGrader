import math
import numpy as np
from services.Config import Config as config
from torch import Tensor
from collections import Counter
import nltk
from nltk.util import ngrams
from nltk.tokenize import word_tokenize
from sklearn.base import BaseEstimator
from sklearn.feature_extraction.text import CountVectorizer
from sentence_transformers import SentenceTransformer, util

nltk.download('punkt_tab')

class CodeClassifier:
    """ Módulo de clasificación """

    def __init__(self, model: BaseEstimator = None, ngram_n = 2):
        self.classifier = model
        self.transformer = SentenceTransformer(config.TOKENIZER)
        self.vectorizer = CountVectorizer(analyzer='word',
                                    tokenizer=word_tokenize,
                                    ngram_range=(ngram_n, ngram_n),
                                    lowercase=False, token_pattern=None)
        self.vocab_ready = False


    def get_embedding(self, code: str) -> Tensor:
        embedding = self.transformer.encode(code, convert_to_tensor=True)
        return embedding
    
    def fit_ngram_vocab(self, codes: list[str]):
        """Debe llamarse una vez antes de usar get_ngram_embedding"""
        self.vectorizer.fit(codes)
        self.vocab_ready = True

    def get_ngram_embedding(self, code: str) -> np.ndarray:
        if not self.vocab_ready:
            raise ValueError("Vectorizer no entrenado. Llama a `fit_ngram_vocab()` primero.")
        vector = self.vectorizer.transform([code]).toarray()[0]
        norm = np.linalg.norm(vector)
        return vector / norm if norm > 0 else vector
    
    
    def euclidean_distance(self, ref1, ref2) -> float: return util.euclidean_sim(ref1, ref2).item()
    def manhattan_distance(self, ref1, ref2) -> float: return util.manhattan_sim(ref1, ref2).item()
    def cosine_similitude(self, ref1, ref2) -> float: return util.pytorch_cos_sim(ref1, ref2).item()