"""
Author: Ali Binkowska
Date: November 2023
Description: chat with today's lunch data
"""
from dotenv import load_dotenv
load_dotenv()
import yaml

from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings

from langchain.vectorstores import Chroma
from langchain.chains import (
    ConversationalRetrievalChain,
)
from langchain.chat_models import ChatOpenAI

from langchain.memory import ChatMessageHistory, ConversationBufferMemory

import chainlit as cl

from utils import (
    get_path,
    date_today,
)

with open('../config.yaml') as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)

template = """Question: {question}
Answer: Let's think step by step."""

@cl.on_chat_start
async def main():
    db_file = get_path('..', cfg['db']['dir'], cfg['db']['vector_db']) + date_today()
    embedding = SentenceTransformerEmbeddings(model_name=cfg['embedding_model_name'])

    docsearch = await cl.make_async(Chroma)(
        persist_directory=db_file,
        embedding_function=embedding,
    )

    message_history = ChatMessageHistory()

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        output_key="answer",
        chat_memory=message_history,
        return_messages=True,
    )

    llm = ChatOpenAI(model_name=cfg['model_name'], temperature=0, streaming=True)

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        chain_type="stuff",
        retriever=docsearch.as_retriever(),
        memory=memory,
        return_source_documents=True,
        verbose=True,
    )

    cl.user_session.set("chain", chain)


@cl.on_message
async def on_message(message: cl.Message):
    chain = cl.user_session.get("chain")
    cb = cl.AsyncLangchainCallbackHandler()

    res = await chain.acall(message.content, callbacks=[cb])
    answer = res['answer']
    print(res)

    await cl.Message(content=answer).send()







