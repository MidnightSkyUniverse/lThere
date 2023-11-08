import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from langchain.vectorstores import Chroma
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from typing import Tuple, List
from operator import itemgetter
from langchain.memory import ConversationBufferMemory
from langchain.vectorstores import Chroma

from langchain.schema.runnable import RunnablePassthrough, RunnableLambda, RunnableMap
from langchain.schema.output_parser import StrOutputParser
from langchain.output_parsers.openai_functions import JsonKeyOutputFunctionsParser
from langchain.prompts.prompt import PromptTemplate
from langchain.prompts import ChatPromptTemplate
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.schema import format_document
from langchain.chains.query_constructor.base import AttributeInfo
from langchain.retrievers.self_query.base import SelfQueryRetriever

###################
# LangChain and LLM
###################

def _embedding_function(model_name: str):
    """Initiate embedding function"""
    return SentenceTransformerEmbeddings(model_name=model_name)

def _llm(chat:bool, temp:int):
    """Return handle to LLM or Chat LLM"""
    return ChatOpenAI(temperature=temp) if chat else OpenAI(temperature=temp)

def _output_parser():
    """return handle for output parser"""
    return StrOutputParser()

def _memory(return_message: bool, output_key: str, input_key: str ):
    """return memory handle"""
    return ConversationBufferMemory(
        return_messages=return_message,
        output_key=output_key,
        input_key=input_key,
    )

def _retriever(llm: str, db: str, document_descr: str, metadata:List):
    """Return retriever handle"""
    return SelfQueryRetriever.from_llm(
        llm,
        db,
        document_descr,
        metadata,
        verbose=True
    )

def _prompt_template(chat: bool, template:str):
    """return formated template"""
    return ChatPromptTemplate.from_template(template) if chat else PromptTemplate.from_template(template)


def metadata_info():
    "return metadata info and document content description"
    metadata_field_info = [
        AttributeInfo(
            name="price",
            description="price of the meal",
            type="string",
        ),
        AttributeInfo(
            name="url",
            description="facebook page of the restaurant",
            type="string",
        ),
    ]
    document_content_description = "lunch menu from local restaurants"

    return metadata_field_info, document_content_description

def _combine_documents(documents):
    formatted_documents = []

    for doc in documents:
        # Assuming 'doc' has 'page_content' and 'metadata' attributes
        page_content = doc.page_content
        price = doc.metadata['price']
        url = doc.metadata['url']
        formatted_doc = f"{page_content} at the price of {price} served by {url}"
        formatted_documents.append(formatted_doc)

    return "\n\n".join(formatted_documents)

###################
# Chroma
###################
def db_connect(db_pth: str, embedding):
    """Return handler to existing Chroma DB"""
    return Chroma(persist_directory=db_pth, embedding_function=embedding)

###################
# Supportive functions
###################
def get_path(*args):
    """get path to the config file"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, *args)

def date_today():
    today = datetime.now().strftime('%Y%m%d')
    # Create a table for today
    return f"{today}"

def load_file(path):
    with open(path) as f:
        return f.read()

