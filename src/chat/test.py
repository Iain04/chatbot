from langchain.schema import HumanMessage, SystemMessage

from langchain.chat_models import ChatOpenAI

from langchain.tools import BaseTool
from typing import Optional, Type
from langchain.agents import initialize_agent, Tool, AgentType
from pydantic import BaseModel, Field
from langchain.prompts import PromptTemplate
from langchain.prompts import MessagesPlaceholder
from langchain.memory import ConversationBufferMemory

from pathlib import Path
from langchain.document_loaders import TextLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import RetrievalQA


from . import webscraping as webscrap    

# Create custom tools
class CheckRoomCheckInput(BaseModel):
    """Input for Hotel room avaliblity."""

    num_adult: int = Field(..., description="The number of adults for the hotel room.")
    num_children: int = Field(..., description="The number of children for the hotel room. If the user did not state the number of children assume the value to be 0.")
    num_rooms: int = Field(..., description="The number of rooms needed for the user. If the user did not state the number of rooms make the value 1.")
    check_in_date: str = Field(..., description="The users check in date of the hotel room. The format must be d-m-y.")
    check_out_date: str = Field(..., description="The users check out date of the hotel room. The format must be d-m-y.")

class CheckRoomTool(BaseTool):
    name = "get_hotel_availability"
    description = "Gets the hotel room availability. Ask for confirmation displaying each value"

    def _run(self, num_adult: int, num_children: int, num_rooms: int, check_in_date: str, check_out_date: str):
        # print("i'm running")
        price_response = webscrap.scape_hotel(num_adult, num_children, num_rooms, check_in_date, check_out_date)

        return price_response

    def _arun(self, num_adult: int, num_children: int, num_rooms: int, check_in_date: str, check_out_date: str):
        raise NotImplementedError("This tool does not support async")

    args_schema: Optional[Type[BaseModel]] = CheckRoomCheckInput


llm = ChatOpenAI(openai_api_key="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", model="gpt-3.5-turbo-0613", temperature=0,)

doc_path = str(Path("C:/Users/iainl/OneDrive/Documents/Year3/MP/Project/src/chat/data.txt"))
loader = TextLoader(doc_path)
documents = loader.load()
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
texts = text_splitter.split_documents(documents)

embeddings = OpenAIEmbeddings(openai_api_key="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")
docsearch = Chroma.from_documents(texts, embeddings, collection_name="data")

search_doc = RetrievalQA.from_chain_type(
    llm=llm, chain_type="stuff", retriever=docsearch.as_retriever()
)


tools = [CheckRoomTool(),
        Tool(
            name="get_doc_info",
            func=search_doc.run,
            description="A document search. Use this only if you cannot answer the question and require more information.",
        ),]


agent_kwargs = {
    "extra_prompt_messages": [MessagesPlaceholder(variable_name="chat_history")],
}
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)


system_message = SystemMessage(
                    content='''You are a laconic assistant for Crowne Plaza Hotel Singapore. 
                    You reply with brief, to-the-point answers with no elaboration.
                    You only reply if the topic is regarding Crowne Plaza Hotel Singapore. 
                    You refuse to reply if the topic is not about Crowne Plaza Hotel Singapore.'''
                )

open_ai_agent = initialize_agent(tools,
                        llm,
                        agent=AgentType.OPENAI_FUNCTIONS,
                        memory=memory,
                        verbose=True,
                        agent_kwargs={
                        "system_message": system_message,
                        "memory": memory
                        })

memory.save_context({"User": "Can you help me check hotel avaliblity"}, {"Assistant": '''Sure, I can help you with that. Please provide me with the following information:
- Number of adults
- Number of children (if any)
- Number of rooms needed
- Check-in date (YYYY-MM-DD)
- Check-out date (YYYY-MM-DD)'''})

response = open_ai_agent.run("2 sep 2023 to 3 sep 2023 for 1 adult")
print(response)

