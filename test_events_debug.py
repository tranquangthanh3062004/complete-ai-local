"""
Debug script to inspect LangGraph astream_events output for intent leak prevention.
"""
import sys
import asyncio

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from services.langgraph_agent import graph_app
from langchain_core.messages import HumanMessage

async def test():
    query = "tôi muốn đi từ triều khúc đến bách khoa"
    print(f"Testing query: '{query}'\n")
    
    async for event in graph_app.astream_events({'messages': [HumanMessage(content=query)]}, version='v1'):
        kind = event.get('event')
        node = event.get('metadata', {}).get('langgraph_node', 'N/A')
        name = event.get('name', 'N/A')
        tags = event.get('tags', [])
        
        if kind in ['on_chat_model_stream', 'on_llm_stream']:
            chunk = event.get('data', {}).get('chunk')
            content = getattr(chunk, 'content', str(chunk))
            print(f"[{kind}] Node: '{node}' | Name: '{name}' | Tags: {tags} | Content: {repr(content)}")

if __name__ == '__main__':
    asyncio.run(test())
