from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. This is our "Messy" Document (A long paragraph)
big_document = """
The Chennai branch of the company follows a strict travel policy. 
Employees must book flights 2 weeks in advance for domestic travel. 
For international travel, 4 weeks notice is required. 
All expense reports must be submitted via the tcs portal within 5 days of returning. 
Failure to follow these rules may result in delayed reimbursements.
"""

# 2. We initialize our "Knife"
# chunk_size = how big each slice is
# chunk_overlap = how much "shared" text is between slices
text_splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)

# 3. Perform the Slicing
chunks = text_splitter.split_text(big_document)

# 4. See the results
print(f"--- Document cut into {len(chunks)} slices ---")
for i, slice in enumerate(chunks):
    print(f"Slice {i+1}: {slice}")
    print("-" * 10)
