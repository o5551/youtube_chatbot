import os
os.environ["OPENAI_API_KEY"] = "your api key"
"""
!pip install -q youtube-transcript-api langchain-community langchain-openai \
               faiss-cpu tiktoken python-dotenv
"""
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
video_id = "Gfr50f6ZBvo" # only the ID, not full URL
try:
    # If you don’t care which language, this returns the “best” one
    transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])

    # Flatten it to plain text
    transcript = " ".join(chunk["text"] for chunk in transcript_list)
    print(transcript)

except TranscriptsDisabled:
    print("No captions available for this video.")

splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.create_documents([transcript])
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vector_store = FAISS.from_documents(chunks, embeddings)
vector_store.index_to_docstore_id
vector_store.get_by_ids(['2436bdb8-3f5f-49c6-8915-0c654c888700'])
## retrieval
 
retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 4})
retriever.invoke('What is stack')     
## Augmentation

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
prompt = PromptTemplate(
    template="""
      You are a helpful assistant.
      Answer ONLY from the provided transcript context.
      If the context is insufficient, just say you don't know.

      {context}
      Question: {question}
    """,
    input_variables = ['context', 'question']
)
question          = "is the topic of nuclear fusion discussed in this video? if yes then what was discussed"
retrieved_docs    = retriever.invoke(question)
retrieved_docs
context_text = "\n\n".join(doc.page_content for doc in retrieved_docs)
context_text
final_prompt = prompt.invoke({"context": context_text, "question": question})
final_prompt
## Generation

answer = llm.invoke(final_prompt)
print(answer.content)
 
## Building a chain

from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
def format_docs(retrieved_docs):
  context_text = "\n\n".join(doc.page_content for doc in retrieved_docs)
  return context_text

parallel_chain = RunnableParallel({
    'context': retriever | RunnableLambda(format_docs),
    'question': RunnablePassthrough()
})

parallel_chain.invoke('how to implement stack using array') 
parser = StrOutputParser()
main_chain = parallel_chain | prompt | llm | parser
main_chain.invoke('Can you summarize the video')

