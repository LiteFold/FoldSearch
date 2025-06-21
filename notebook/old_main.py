import openai
from dotenv import load_dotenv
from notebook.protein_search import (
    RCSB_SEARCH_API_TOOL_DESCRIPTIONS,
    SearchAPIUnifiedResults
)
import json

from pydantic import BaseModel

load_dotenv()

client = openai.OpenAI()

planner_prompt = f""""
You are very efficient biotechnologist who works on protein engineering and drug design. You will be given a list of tools as follows: {RCSB_SEARCH_API_TOOL_DESCRIPTIONS}

Based on the user query, you need to output a list of tool keys to use in sequential format. The tool keys must be EXACTLY as they appear in the dictionary (e.g., "high_quality_structures_tool", "text_search_tool", etc.). Ensure you use minimal number of tools to get the result.
"""
tool_using_prompt = f""""
You are very efficient biotechnologist who works on protein engineering and drug design. You will be given a list of tools as follows: {RCSB_SEARCH_API_TOOL_DESCRIPTIONS}

Now you will also be given the tool that you need to use now. Ensure you make the
correct arguments for the tool. 
"""


class ToolUsageResult(BaseModel):
    tools_to_use: list[str]


def find_tools_to_use(query: str) -> list[str]:
    model = "gpt-4o-mini"
    messages = [
        {"role": "system", "content": planner_prompt},
        {"role": "user", "content": query}
    ]
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=messages,
        response_format=ToolUsageResult
    )
    return completion.choices[0].message.parsed.tools_to_use


def get_tool_argument(query: str, using_tool: str):
    messages = [
        {"role": "system", "content": tool_using_prompt},
        {"role": "user", "content": query}
    ]
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=[using_tool]
    )
    return completion, messages



def search(query: str):
    tools_to_use = find_tools_to_use(query=query)
    tool_results = {}
    llm_result = []

    for tool in tools_to_use:
        print(f"\nProcessing tool: {tool}")
        
        print("Getting tool arguments...")
        result, messages = get_tool_argument(
            query=query,
            using_tool=RCSB_SEARCH_API_TOOL_DESCRIPTIONS[tool]["tool"]
        )
        
        print("Extracting tool call and arguments...")
        tool_call = result.choices[0].message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        print(f"Arguments: {args}")
        
        print("Executing tool function...")
        tool_result = RCSB_SEARCH_API_TOOL_DESCRIPTIONS[tool]["function"](**args)
        tool_results[tool] = tool_result
        
        # Add assistant message with tool call
        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [tool_call]
        })
        
        # Add tool response message
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": str(tool_result)
        })
        
        print("Getting LLM completion for tool result...")
        llm_completion_from_tool = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=[RCSB_SEARCH_API_TOOL_DESCRIPTIONS[tool]["tool"]]
        )
        llm_result.append(llm_completion_from_tool.choices[0].message.content)
        print("LLM completion received")
    
    print("\nAll tools processed")


    final_prompt = """"
    Given the set of results and the user query, summarize the final answer in almost 2-3 sentences. Here is the user query {query} and here is the results
    w.r.t. different tools {results}
    """

    final_message = [{
        "role": "user", "content": final_prompt.format(
            query=query,
            results=tool_results
        )
    }]
    completion = client.chat.completions.create(messages=final_message, model="gpt-4o-mini")

    return tool_results, completion.choices[0].message.content




if __name__ == '__main__':
    query = "find high-quality structures of human hemoglobin with good resolution"

    tool_results, llm_result = search(query=query)
    print(tool_results)
    print(llm_result)


