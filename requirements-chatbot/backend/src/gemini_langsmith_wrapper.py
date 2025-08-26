from typing import Any, Dict, List, Optional, Union
from langsmith import traceable
KVMap = Dict[str, Any]

"""
Thanks to https://github.com/langchain-ai/langsmith-sdk/issues/1722#issuecomment-3146440473 and Claude Code
Example Usage:

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from .gemini_langsmith_wrapper import wrap_gemini

search_tool = TavilySearch(max_results=1)
llm = wrap_gemini(ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.5,
            max_retries=2,
            )).bind_tools([search_tool])

llm.invoke("Hellow world")

# Or in a node of Langraph
def _chatbot_node(self, state: State) -> Dict[str, Any]:
        response = self.llm.invoke(state["messages"])
        return {"messages": [response]}
"""

class PatchedGeminiClient:
    """Wrapper for Google GenAI client with LangSmith tracing."""
    
    def __init__(self, original_client: Any, options: Optional[Dict[str, Any]] = None):
        self.original_client = original_client
        self.options = options or {}
        
        if hasattr(original_client.invoke, '_langsmith_traced'):
            raise ValueError(
                "This instance of Google GenAI client has been already wrapped once."
            )
        
        self.invoke = self._create_traced_generate_content()
    
    def _create_traced_generate_content(self):
        """Create a traced version of the generate_content method."""
        @traceable(
            name="ChatGemini",
            run_type="llm",
            **self.options
        )
        def traced_generate_content(
            contents: Union[str, List[Dict[str, Any]]],
            model: str,
            generation_config: Optional[Dict[str, Any]] = None,
            langsmith_extra: Optional[Dict[str, Any]] = None,
            **kwargs
        ):
            request_params = {
                "contents": contents,
                "model": model,
                **kwargs
            }
            
            if generation_config:
                request_params["generation_config"] = generation_config
            
            # Add langsmith metadata if provided
            if langsmith_extra:
                # This would be handled by the traceable decorator
                pass
            
            # Call the original method
            response = self.original_client.invoke(**request_params)
            
            return response
        
        # Mark as traced to prevent double wrapping
        traced_generate_content._langsmith_traced = True
        
        return traced_generate_content
    
    def __getattr__(self, name):
        """Delegate other attributes to the original client."""
        return getattr(self.original_client, name)


def _combine_gemini_content_chunks(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Combine multiple Gemini response chunks into a single response."""
    if not chunks:
        return {"candidates": [{"content": {"parts": [{"text": ""}]}}]}
    
    aggregated_output = chunks[-1].copy()
    combined_text = ""
    
    for chunk in chunks:
        candidates = chunk.get("candidates", [])
        if candidates and len(candidates) > 0:
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            for part in parts:
                if "text" in part and part["text"]:
                    combined_text += part["text"]
    
    # Update the final chunk with the combined text
    if (aggregated_output.get("candidates") and 
        len(aggregated_output["candidates"]) > 0 and
        aggregated_output["candidates"][0].get("content", {}).get("parts")):
        aggregated_output["candidates"][0]["content"]["parts"] = [{"text": combined_text}]
    
    return aggregated_output


def gemini_aggregator(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    return _combine_gemini_content_chunks(chunks)


def process_gemini_completion(outputs: KVMap) -> KVMap:
    """Process Gemini completion outputs for LangSmith."""
    gemini_response = outputs.get("outputs", {})
    
    # Extract the text content from the response
    text_content = ""
    candidates = gemini_response.get("candidates", [])
    if candidates and len(candidates) > 0:
        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        if parts and len(parts) > 0:
            text_content = parts[0].get("text", "")
    
    # Return in chat-like format that LangSmith expects
    result = {
        "content": text_content,
        "role": "assistant"
    }
    
    # Add usage metadata if available
    usage_metadata = gemini_response.get("usageMetadata") or gemini_response.get("usage_metadata")
    if usage_metadata:
        result["usage_metadata"] = {
            "input_tokens": usage_metadata.get("promptTokenCount", 0),
            "output_tokens": usage_metadata.get("candidatesTokenCount", 0),
            "total_tokens": usage_metadata.get("totalTokenCount", 0),
            "output_token_details": {
                "reasoning": usage_metadata.get("thoughtsTokenCount", 0),
            },
        }
    
    return result


def process_gemini_inputs(inputs: KVMap) -> KVMap:
    """Process Gemini inputs for LangSmith."""
    contents = inputs.get("contents")
    
    if not contents or not isinstance(contents, list):
        return inputs
    
    # Convert to chat-like format that LangSmith expects
    messages = []
    
    for content in contents:
        role = content.get("role", "user")
        parts = content.get("parts", [])
        
        text_parts = [part for part in parts if "text" in part and part.get("text")]
        image_parts = [part for part in parts if "inlineData" in part]
        
        converted_parts = []
        
        # Add text parts
        if text_parts:
            message_content = "\n".join(part["text"] for part in text_parts)
            converted_parts.append({
                "type": "text",
                "text": message_content
            })
        
        # Add image parts in LangSmith-compatible format
        for part in image_parts:
            inline_data = part["inlineData"]
            converted_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{inline_data['mimeType']};base64,{inline_data['data']}",
                    "detail": "high"
                }
            })
        
        # Determine message content format
        if len(converted_parts) == 1 and converted_parts[0]["type"] == "text":
            message_content = converted_parts[0]["text"]
        else:
            message_content = converted_parts
        
        messages.append({
            "role": role,
            "content": message_content
        })
    
    result = {
        "messages": messages,
        "model": inputs.get("model")
    }
    
    if "config" in inputs:
        result["config"] = inputs["config"]
    
    return result


def get_invocation_params(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract invocation parameters from the payload."""
    if not isinstance(payload, dict):
        return None
    
    # Extract stop sequences if they exist in generation config
    ls_stop = None
    generation_config = payload.get("generation_config", {})
    if generation_config and "stop_sequences" in generation_config:
        ls_stop = generation_config["stop_sequences"]
    
    return {
        "ls_provider": "google",
        "ls_model_type": "chat",
        "ls_model_name": payload.get("model"),
        "ls_max_tokens": generation_config.get("max_output_tokens"),
        "ls_temperature": generation_config.get("temperature"),
        "ls_stop": ls_stop,
    }


def wrap_gemini(gemini_client: Any, options: Optional[Dict[str, Any]] = None) -> PatchedGeminiClient:
    # Merge default options
    default_options = {
        "aggregator": gemini_aggregator,
        "process_inputs": process_gemini_inputs,
        "process_outputs": process_gemini_completion,
        "get_invocation_params": get_invocation_params,
    }
    
    if options:
        default_options.update(options)
    
    return PatchedGeminiClient(gemini_client, default_options)