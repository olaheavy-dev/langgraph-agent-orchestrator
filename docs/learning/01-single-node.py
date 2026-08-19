import uuid
from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

llm = init_chat_model('openai:gpt-4.1-mini')

def prompt_llm(state: MessagesState):
    response = llm.invoke(state['messages'])
    return {'messages': [response]}

graph_builder = StateGraph(MessagesState)

graph_builder.add_node(prompt_llm)
graph_builder.add_edge(START, 'prompt_llm')
graph_builder.add_edge('prompt_llm', END)

checkpointer = InMemorySaver()
graph = graph_builder.compile(checkpointer=checkpointer)

def main():
    config: RunnableConfig = {'configurable': {'thread_id': str(uuid.uuid4())}}

    while True:
        user_input = input('You: ')
        if user_input.strip().lower() in {'quit', 'exit'}:
            break

        state = graph.invoke({'messages': [HumanMessage(user_input)]}, config)
        print(f'Assistant: {state["messages"][-1].text}')

if __name__ == '__main__':
    main()
