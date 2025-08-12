from sentence_transformers import SentenceTransformer, util
import torch
import json
import os
from utils import get_models_dir, get_viewer_assets

class ModelSelector:
    def __init__(self):
        model_path = os.path.join(get_models_dir(), "all-MiniLM-L6-v2")
        self.model = SentenceTransformer(model_path)

        self.desc_file = os.path.join(get_viewer_assets(), "model_descriptions.json")
        self.model_descriptions = self.load_descriptions(self.desc_file)
        self.descriptions = list(self.model_descriptions.values())
        self.embeddings = self.model.encode(self.descriptions, convert_to_tensor=True)
    
    def load_descriptions(self, filepath):
        try:
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and len(data) > 0:
                        return data
        except Exception as e:
            print(f"Failed to load descriptions from {filepath}: {e}")
        return {}

    def save_descriptions(self):
        os.makedirs(os.path.dirname(self.desc_file), exist_ok=True)
        with open(self.desc_file, "w", encoding="utf-8") as f:
            json.dump(self.model_descriptions, f, indent=2)

    def add_model(self, filename, description):
        self.model_descriptions[filename] = description
        self.save_descriptions()
        self.descriptions = list(self.model_descriptions.values())
        self.embeddings = self.model.encode(self.descriptions, convert_to_tensor=True)

    def remove_model(self, filename):
        if filename in self.model_descriptions:
            del self.model_descriptions[filename]
            self.save_descriptions()
            self.descriptions = list(self.model_descriptions.values())
            self.embeddings = self.model.encode(self.descriptions, convert_to_tensor=True)

    def get_best_match(self, input_text, threshold=0.5):
        query_embedding = self.model.encode(input_text, convert_to_tensor=True)
        scores = util.cos_sim(query_embedding, self.embeddings)[0]
        best_score = torch.max(scores).item()
        best_idx = torch.argmax(scores).item()

        if best_score < threshold:
            return None, best_score
        
        filename = list(self.model_descriptions.keys())[best_idx]
        print("Filename:", filename)

        model_path = os.path.join(get_viewer_assets(), "3d_assets", filename)

        if os.path.isfile(model_path):
            print("Model path:", model_path, "Best score:", best_score)
            return model_path, best_score
        else:
            return None, 0.0
