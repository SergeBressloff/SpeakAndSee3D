from sentence_transformers import SentenceTransformer

# Download and save the model to a specific directory
model = SentenceTransformer('all-MiniLM-L6-v2')
model.save('./bin/models/all-MiniLM-L6-v2')