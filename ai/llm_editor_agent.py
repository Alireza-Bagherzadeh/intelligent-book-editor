import json
from typing import List, TypedDict, Dict
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END

from persian_text_pipeline import PersianTextPipeline, ProcessingResult


# ====================================================================
# 1. Pydantic Schemas for Structured LLM Output
# ====================================================================
class ErrorDecision(BaseModel):
    log_index: int = Field(..., description="Index ID of the error segment being evaluated")
    is_original_correct: bool = Field(..., description="Whether the original word is correct and needs no change")
    confidence: int = Field(..., description="Confidence level score between 0 and 100")
    selected_word: str = Field(..., description="The final selected/corrected Persian word")

class LLMBatchResponse(BaseModel):
    decisions: List[ErrorDecision] = Field(..., description="List of decisions for all provided errors in this batch")


# ====================================================================
# 2. Graph State Definition
# ====================================================================
class GraphState(TypedDict):
    pipeline_result: ProcessingResult
    pending_indices: List[int]
    batch_size: int
    model_name: str


# ====================================================================
# 3. LangGraph Nodes
# ====================================================================
def prepare_batches_node(state: GraphState) -> GraphState:
    """Filter errors that require LLM evaluation."""
    result = state["pipeline_result"]
    pending = []

    for idx, log in enumerate(result.change_logs):
        ctype = log.change_type.value if hasattr(log.change_type, 'value') else str(log.change_type)
        if ctype in ["SUGGESTED_FIX", "SUSPECT_TYPO", "AMBIGUOUS"]:
            pending.append(idx)

    return {"pending_indices": pending}

def process_llm_batch_node(state: GraphState) -> GraphState:
    """Process a batch of errors with Ollama using structured output."""
    pending = state["pending_indices"]
    batch_size = state["batch_size"]
    result = state["pipeline_result"]

    current_batch_indices = pending[:batch_size]

    batch_data = []
    for idx in current_batch_indices:
        log = result.change_logs[idx]
        batch_data.append({
            "log_index": idx,
            "change_type": log.change_type.value if hasattr(log.change_type, 'value') else str(log.change_type),
            "original_segment": log.original_segment,
            "suggestions": log.suggestions,
            "context": log.context.full_context if log.context else ""
        })

    batch_json_str = json.dumps(batch_data, ensure_ascii=False, indent=2)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert Persian language editor and proofreader.
Your task is to review potential Persian text errors and select the correct Persian word.
For each error provided in JSON format:
1. If the original Persian word is correct (e.g., proper nouns), set is_original_correct to true and keep selected_word as the original word.
2. If the word is misspelled, select the best option from suggestions based on context. If suggestions are invalid, infer the correct Persian word yourself.
3. For half-space suggestions (SUGGESTED_FIX), determine if a half-space (zwnj) is required in this Persian context and set selected_word accordingly."""),
        ("human", "List of errors to evaluate:\n{batch_json}")
    ])

    llm = ChatOllama(model=state["model_name"], temperature=0.0, reasoning=False)
    structured_llm = llm.with_structured_output(LLMBatchResponse)

    chain = prompt | structured_llm

    try:
        response: LLMBatchResponse = chain.invoke({"batch_json": batch_json_str})

        for decision in response.decisions:
            idx = decision.log_index
            # Populate the llm_choice field directly in the original structure
            result.change_logs[idx].llm_choice = decision.selected_word

    except Exception as e:
        print(f"[LLM Processing Error]: {e}")

    remaining_pending = pending[batch_size:]
    return {
        "pending_indices": remaining_pending,
        "pipeline_result": result
    }

def apply_llm_corrections_node(state: GraphState) -> GraphState:
    """Reconstruct the final text by applying LLM choices over original change logs."""
    result = state["pipeline_result"]
    # Re-apply corrections using LLM decisions
    result.corrected_text = PersianTextPipeline.apply_llm_corrections(result)
    return {"pipeline_result": result}


# ====================================================================
# 4. Graph Definition & Execution
# ====================================================================
def should_continue(state: GraphState):
    if len(state["pending_indices"]) == 0:
        return "apply_corrections"
    return "llm_batch_processor"

workflow = StateGraph(GraphState)
workflow.add_node("prepare", prepare_batches_node)
workflow.add_node("llm_batch_processor", process_llm_batch_node)
workflow.add_node("apply_corrections", apply_llm_corrections_node)

workflow.set_entry_point("prepare")
workflow.add_edge("prepare", "llm_batch_processor")
workflow.add_conditional_edges(
    "llm_batch_processor",
    should_continue,
    {
        "llm_batch_processor": "llm_batch_processor",
        "apply_corrections": "apply_corrections"
    }
)
workflow.add_edge("apply_corrections", END)

app = workflow.compile()