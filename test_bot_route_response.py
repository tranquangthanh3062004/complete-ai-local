"""
Test direct_chat output for Triệu Khúc -> Bách Khoa query.
"""
import sys
import asyncio

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from services.langgraph_agent import graph_app
from langchain_core.messages import HumanMessage

async def main():
    print("=" * 60)
    print("  Testing LangGraph Agent: Triều Khúc -> Bách Khoa")
    print("=" * 60)

    query = "Làm thế nào để đi bằng phương tiện công cộng từ Triều Khúc đến Đại học Bách Khoa?"
    state_input = {
        "messages": [HumanMessage(content=query)],
        "temperature": 0.1
    }

    res = await graph_app.ainvoke(state_input)
    msg = res["messages"][-1]
    answer = msg.content if hasattr(msg, "content") else str(msg)

    print("\n[BOT RESPONSE]:")
    print(answer)
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
