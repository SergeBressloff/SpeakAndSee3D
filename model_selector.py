from sentence_transformers import SentenceTransformer, util
import torch
import json
import os
from utils import resource_path, get_writable_viewer_assets

class ModelSelector:
    def __init__(self, desc_file = os.path.join(get_writable_viewer_assets(), "model_descriptions.json")):
        # Need to put sentence transformer model in bin/models
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.desc_file = resource_path(desc_file)

        self.model_descriptions = self.load_descriptions_from_multiple_sources()
        self.descriptions = list(self.model_descriptions.values())
        self.embeddings = self.model.encode(self.descriptions, convert_to_tensor=True)
    
    # Maybe need to copy over viewer_assets once, when the app first loads in main.py
    # Then always load everything from writable_viewer_assets?
    def load_descriptions_from_multiple_sources(self):
        bundled = self.load_descriptions(resource_path(os.path.join("viewer_assets", "model_descriptions.json")))
        user = self.load_descriptions(os.path.join(get_writable_viewer_assets(), "model_descriptions.json"))
        return {**bundled, **user}
    
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

    def get_best_match(self, input_text, threshold=0.5):
        query_embedding = self.model.encode(input_text, convert_to_tensor=True)
        scores = util.cos_sim(query_embedding, self.embeddings)[0]
        best_score = torch.max(scores).item()
        print("Best score:", best_score)
        best_idx = torch.argmax(scores).item()

        if best_score < threshold:
            return None, best_score
        
        filename = list(self.model_descriptions.keys())[best_idx]
        print("Filename:", filename)

        bundled_path = resource_path(os.path.join("viewer_assets", "3d_models", filename))
        print("Bundled path:", bundled_path)
        user_path = os.path.join(get_writable_viewer_assets(), "3d_models", filename)
        print("User path:", user_path)

        if os.path.isfile(user_path):
            print("User path:", user_path, "Best score:", best_score)
            return user_path, best_score
        elif os.path.isfile(bundled_path):
            print("Bundled path:", bundled_path, "Best score:", best_score)
            return bundled_path, best_score
        else:
            return None, 0.0
