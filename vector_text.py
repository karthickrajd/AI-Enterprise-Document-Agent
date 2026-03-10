from sentence_transformers import SentenceTransformer

# 1. Load the "Scanner" (This will download a small model the first time)
model = SentenceTransformer("all-MiniLM-L6-v2")

# 2. Two sentences that mean the same thing but use different words
sentences = [
    "How do I get my money back for travel?",
    "What is the procedure for expense reimbursement?",
]

# 3. Turn them into Vectors (GPS Addresses)
vectors = model.encode(sentences)

print(f"Vector for Sentence 1 (First 5 numbers): {vectors[0][:5]}")
print(f"Vector for Sentence 2 (First 5 numbers): {vectors[1][:5]}")
