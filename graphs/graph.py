import asyncio
from langgraph.graph import StateGraph, START, END
from tools.finalizetool import Finalize
from state.state import ContentState
from tools.bodytool import giveBody
from tools.conclusiontool import giveConclusion
from tools.introtool import giveIntroduction


async def build_Agentic_Graph(data):
    graph_builder = StateGraph(ContentState)

    graph_builder.add_node("intro_Agent", giveIntroduction)
    graph_builder.add_node("body_Agent", giveBody)
    graph_builder.add_node("conclusion_Agent", giveConclusion)
    graph_builder.add_node("PPT_Agent", Finalize)

    graph_builder.add_edge(START, "intro_Agent")
    graph_builder.add_edge(START, "body_Agent")
    graph_builder.add_edge(START, "conclusion_Agent")

    graph_builder.add_edge("intro_Agent", "PPT_Agent")
    graph_builder.add_edge("body_Agent", "PPT_Agent")
    graph_builder.add_edge("conclusion_Agent", "PPT_Agent")

    graph_builder.add_edge("PPT_Agent", END)

    graph = graph_builder.compile()

    output = await graph.ainvoke({'messages': [{"role": "user", "content": data}]})

    return output
