"""
Author: Ali Binkowska
Date: November 2023
Description: chat with today's lunch data
"""
from dotenv import load_dotenv
load_dotenv()
import yaml

from langchain.vectorstores import Chroma
from langchain.schema.runnable import (
    RunnablePassthrough,
    RunnableLambda,
    RunnableMap,
    RunnableConfig
)
from operator import itemgetter
import chainlit as cl

from utils import (
    get_path,
    load_file,
    date_today,
    metadata_info,
    _embedding_function,
    _llm,
    _output_parser,
    _memory,
    _retriever,
    _prompt_template,
    _combine_documents,
)

with open('../config.yaml') as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)


@cl.on_chat_start
async def main():
    # initiate asynchronous connection to vectorstore
    db_file = get_path('..', cfg['db']['dir'], cfg['db']['vector_db']) + date_today()
    embedding = _embedding_function(model_name=cfg['embedding_model_name'])
    docsearch = await cl.make_async(Chroma)(
        persist_directory=db_file,
        embedding_function=embedding,
    )

    # memory
    memory = _memory(return_message=False, output_key="answer", input_key="question" )

    llm = _llm(chat=False, temp=0)
    chat_llm = _llm(chat=True, temp=0)
    output_parser = _output_parser()

    metadata_field_info, document_content_description = metadata_info()

    # retriever
    retriever = _retriever(llm, docsearch, document_content_description, metadata_field_info)

    _template =  load_file(get_path('..', cfg['prompts']['dir'], cfg['prompts']['condense']))
    CONDENSE_QUESTION_PROMPT = _prompt_template(chat= False, template=_template)

    template = load_file(get_path('..', cfg['prompts']['dir'], cfg['prompts']['answer']))
    ANSWER_PROMPT = _prompt_template(chat=True, template=template)


    # chain elements
    standalone_question = {
        "standalone_question": {
                                   "question": lambda x: x["question"],
                                   "chat_history": lambda x: x["chat_history"],
                               }
                               | CONDENSE_QUESTION_PROMPT
                               | chat_llm
                               | output_parser,
    }

    # This adds a "memory" key to the input object
    loaded_memory = RunnablePassthrough.assign(
        chat_history=RunnableLambda(memory.load_memory_variables) | itemgetter("history"),
    )


    retrieved_documents = RunnableMap({
        "docs": lambda x: retriever.get_relevant_documents(itemgetter("standalone_question")),
        "question": lambda x: x["standalone_question"],
    })

    final_inputs = {
        "context": lambda x: _combine_documents(x["docs"]),
        "question": itemgetter("question"),
    }

    runnable = (
            loaded_memory
            | standalone_question
            | retrieved_documents
            | final_inputs
             | ANSWER_PROMPT
             | chat_llm
             | output_parser
             )

    cl.user_session.set("runnable", runnable)


@cl.on_message
async def on_message(message: cl.Message):
    runnable = cl.user_session.get("runnable")

    msg = cl.Message(content="")

    async for chunk in runnable.astream(
            {"question": message.content},
            config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
    ):
        await msg.stream_token(chunk)

    await msg.send()









