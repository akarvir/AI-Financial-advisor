import os
from dotenv import load_dotenv
from langchain_community.document_loaders import (
    PyPDFLoader,
    PyMuPDFLoader, 
    PDFMinerLoader,
    PyPDFium2Loader
)
from langchain_postgres.vectorstores import PGVector
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings

load_dotenv()
docsdir = os.path.abspath("../sourcedocs")
allfilepaths = []

for each in os.listdir(docsdir):
    if(each.lower().endswith('.pdf')):
        allfilepaths.append(os.path.join(docsdir,each))

# trying different loaders for each of the pdfs

alldocs = []
pdf_count  = 0
print(f"All the file paths are {allfilepaths}")

for pdffile in allfilepaths:

    bestcontent = ""
    bestloadername = None
    bestdocs = []

    # let's try PDFLoader
    try:
        loader = PyPDFLoader(pdffile)
        docs = loader.load() # returns list of document objects, by default splits pdf by page
        content = " ".join([doc.page_content for doc in docs]) # takes all page content retrieved from all pages, and appends them together
        if(len(content)>len(bestcontent)):
            bestcontent = content
            bestloadername = "PyPDFLoader"
            bestdocs = docs
    except Exception as e:
        print(f"PyPDFLoader failed: {e}")

    
    try:
        loader = PyMuPDFLoader(pdffile)
        docs = loader.load() # returns list of document objects, by default splits pdf by page
        content = " ".join([doc.page_content for doc in docs]) # takes all page content retrieved from all pages, and appends them together
        if(len(content)>len(bestcontent)):
            bestcontent = content
            bestloadername = "PyMuPDFLoader"
            bestdocs = docs
    except Exception as e:
        print(f"PyMuPDFLoader failed: {e}")
    
    try:
        loader = PDFMinerLoader(pdffile)
        docs = loader.load() # returns list of document objects, by default splits pdf by page
        content = " ".join([doc.page_content for doc in docs]) # takes all page content retrieved from all pages, and appends them together
        if(len(content)>len(bestcontent)):
            bestcontent = content
            bestloadername = "PDFMinerLoader"
            bestdocs = docs
    except Exception as e:
        print(f"PDFMinerLoader failed: {e}")

    
    try:
        loader = PyPDFium2Loader(pdffile)
        docs = loader.load() # returns list of document objects, by default splits pdf by page
        content = " ".join([doc.page_content for doc in docs]) # takes all page content retrieved from all pages, and appends them together
        if(len(content)>len(bestcontent)):
            bestcontent = content
            bestloadername = "PyPDFium2Loader"
            bestdocs = docs
    except Exception as e:
        print(f"PyPDFium2Loader failed: {e}")

    print(f"The best loader is {bestloadername} with {len(bestcontent)} characters.")

    if(len(bestcontent)>100):

        pdf_count+=1
        print(f"The number of valid pdfs now are: {pdf_count} ")
        alldocs.extend(bestdocs) # this pdf will be added to the whole collection for all pdfs, because there is some relevant information in this pdf, best content is all added up
        print(f"Content preview: {bestcontent[:200]}....")
    else:
        print(" CONTENT is too little, pdf might be empty")
    
# Splitting the docs into manageable chunks, textsplitter still return document objects, but with smaller page content and optional overlap in text content

print("Splitting documents into chunks:")
text_splitter = RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap = 200)
chunks = text_splitter.split_documents(alldocs)

# Storing in vector database

print("Now storing in postgres with vector extension created")

embedding = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'}  # or 'cuda' if you have GPU
)

#PGVector.from_documents: Return VectorStore initialized from documents and embeddings.

# Use the connection string directly since we're using psycopg2
vectorstore = PGVector.from_documents(documents=chunks, embedding=embedding, collection_name="rag_chunks", connection=os.getenv("PGVECTOR_CONNECTION_STRING"), pre_delete_collection=True)

print("Documents processed and stored successfully!")
