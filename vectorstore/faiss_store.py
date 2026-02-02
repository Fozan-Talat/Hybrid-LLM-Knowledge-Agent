import os
import faiss
import pickle
import numpy as np
from app.config import FAISS_INDEX_PATH, METADATA_PATH

class FaissStore:
    def __init__(self, dim=3072):
        self.index = faiss.IndexFlatL2(dim)
        self.metadata = []

    def add(self, vectors, meta):
        self.index.add(np.array(vectors).astype("float32"))
        self.metadata.extend(meta)

    def search(self, query_vec, k=5):
        D, I = self.index.search(
            np.array([query_vec]).astype("float32"), k
        )
        return [self.metadata[i] for i in I[0]]

    def save(self):
        os.makedirs(os.path.dirname(FAISS_INDEX_PATH), exist_ok=True)
        faiss.write_index(self.index, FAISS_INDEX_PATH)
        pickle.dump(self.metadata, open(METADATA_PATH, "wb"))

    def load(self):
        if not os.path.exists(FAISS_INDEX_PATH):
            raise FileNotFoundError("FAISS index not found")
        
        self.index = faiss.read_index(FAISS_INDEX_PATH)
        self.metadata = pickle.load(open(METADATA_PATH, "rb"))
