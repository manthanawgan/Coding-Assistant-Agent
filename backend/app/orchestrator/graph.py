from langgraph.graph import StateGraph, END
from app.orchestrator.state import AgentState, create_initial_state
from app.orchestrator.supervisor import SupervisorAgent
from app.config.logging import logger


def create_workflow_graph():
    builder = StateGraph(AgentState)

    builder.add_node("supervisor", supervisor_node)
    builder.add_node("research", research_node)
    builder.add_node("context", context_node)
    builder.add_node("coding", coding_node)
    builder.add_node("testing", testing_node)
    builder.add_node("security", security_node)
    builder.add_node("approval", approval_node)
    builder.add_node("pr_creation", pr_creation_node)
    builder.add_node("failed", failed_node)

    builder.set_entry_point("supervisor")

    builder.add_edge("supervisor", "research")
    builder.add_edge("research", "context")
    builder.add_edge("context", "coding")
    builder.add_edge("coding", "testing")
    builder.add_edge("testing", "security")

    builder.add_conditional_edges(
        "testing",
        lambda state: "retry" if state.get("test_results", {}).get("status") == "failed" else "continue",
        {"retry": "coding", "continue": "security"}
    )

    builder.add_conditional_edges(
        "security",
        lambda state: "failed" if not state.get("security_results", {}).get("passed") else "approval",
        {"failed": "failed", "continue": "approval"}
    )

    builder.add_conditional_edges(
        "approval",
        lambda state: "pr_creation" if state.get("human_approved") else "approval",
        {"pr_creation": "pr_creation", "continue": "approval"}
    )

    builder.add_edge("pr_creation", END)
    builder.add_edge("failed", END)

    return builder.compile()


supervisor = SupervisorAgent()


async def supervisor_node(state: AgentState) -> AgentState:
    logger.info(f"Supervisor processing task {state.get('task_id')}")
    result = await supervisor.execute(state)
    return {**state, **result}


async def research_node(state: AgentState) -> AgentState:
    state["current_agent"] = "research"
    return state


async def context_node(state: AgentState) -> AgentState:
    state["current_agent"] = "context"
    return state


async def coding_node(state: AgentState) -> AgentState:
    state["current_agent"] = "coding"
    return state


async def testing_node(state: AgentState) -> AgentState:
    state["current_agent"] = "testing"
    return state


async def security_node(state: AgentState) -> AgentState:
    state["current_agent"] = "security"
    return state


async def approval_node(state: AgentState) -> AgentState:
    state["current_agent"] = "approval"
    return state


async def pr_creation_node(state: AgentState) -> AgentState:
    state["current_agent"] = "pr_creation"
    result = await supervisor.create_pr(state)
    return {**state, "pr_results": result, "status": "completed"}


async def failed_node(state: AgentState) -> AgentState:
    state["current_agent"] = "failed"
    state["status"] = "failed"
    return state


workflow = create_workflow_graph()
