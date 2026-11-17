from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class LocalSemanticAnalyzer:
    """
    Privacy-preserving local semantic analyzer.
    Uses scikit-learn TF-IDF vectorization and cosine similarity for concept comparison.
    Zero external API calls, operates 100% locally and offline.
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            token_pattern=r'(?u)\b\w+\b',
            ngram_range=(1, 2)
        )

    def compute_similarity(self, text_a: str, text_b: str) -> float:
        """Computes pairwise cosine similarity between two text snippets."""
        if not text_a or not text_b:
            return 0.0

        if text_a.strip().lower() == text_b.strip().lower():
            return 1.0

        try:
            tfidf_matrix = self.vectorizer.fit_transform([text_a, text_b])
            sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(round(sim, 4))
        except Exception:
            # Fallback to Jaccard token similarity if vocabulary is too small
            words_a = set(text_a.lower().split())
            words_b = set(text_b.lower().split())
            if not words_a or not words_b:
                return 0.0
            return float(round(len(words_a & words_b) / len(words_a | words_b), 4))

    def find_best_semantic_match(
        self,
        query: str,
        candidates: List[str]
    ) -> Tuple[Optional[str], float, int]:
        """
        Finds the highest similarity candidate for a given query text.
        Returns: (best_candidate_text, similarity_score, candidate_index)
        """
        if not candidates or not query:
            return None, 0.0, -1

        try:
            corpus = [query] + candidates
            tfidf_matrix = self.vectorizer.fit_transform(corpus)
            query_vec = tfidf_matrix[0:1]
            cand_matrix = tfidf_matrix[1:]

            sims = cosine_similarity(query_vec, cand_matrix)[0]
            best_idx = int(np.argmax(sims))
            best_score = float(round(sims[best_idx], 4))

            return candidates[best_idx], best_score, best_idx
        except Exception:
            return None, 0.0, -1
