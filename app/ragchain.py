import os 
from operator import itemgetter
from typing import TypedDict
from dotenv import load_dotenv
from langchain_postgres.vectorstores import PGVector
from langchain.prompts import PromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.runnables.base import RunnableParallel
from langchain_community.llms import LlamaCpp
from langchain_core.documents import Document

# remember to use PromptTemplate, since it is a text completion agent not a conversational agent, it is stateless.
load_dotenv()

os.environ["LLAMA_CPP_LOG_LEVEL"] = "ERROR" 

embedding = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'}  # or 'cuda' if you have GPU
)

vector_store = PGVector(collection_name = os.getenv("PG_COLLECTION_NAME"),connection = os.getenv("PGVECTOR_CONNECTION_STRING"),embeddings = embedding)

llm = LlamaCpp(
    model_path="/Users/Anshu/.ollama/models/blobs/sha256-8934d96d3f08982e95922b2b7a2c626a1fe873d7c3b06e8e56d7bc0a1fef9246",
    n_ctx=4096,
    temperature=0.7,
    max_tokens = 1024
)

ANSWER_PROMPT = PromptTemplate.from_template(
    """You are an assistant who is knowledgeable about India's current economic trajectory. Given the context below, only with sentences or passages, no latex or code. 

Context:
{context}

Question:
{question}

Detailed Answer(in plain English):"""
)

input_dict = {"question": "Summary of 2025 India equity market outlook"}

class RagInput(TypedDict):
    question: str

final_chain = (
    RunnableParallel(  # This part fetches the context and passes the question
        context=itemgetter("question") | vector_store.as_retriever(),
        question=itemgetter("question")
    ) |
    RunnableParallel(  # This part generates the answer using the prompt and llm
        answer=ANSWER_PROMPT | llm,
        docs=itemgetter("context")
    )
).with_types(input_type=RagInput)

