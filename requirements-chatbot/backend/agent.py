
from typing import Annotated, List, Dict, Any, AsyncIterator
from typing_extensions import TypedDict

from fastapi import HTTPException
from pydantic import BaseModel
import json

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage

GEMINI_FLASH="google_genai:gemini-2.0-flash"
MODEL=GEMINI_FLASH

class State(TypedDict):
    messages: Annotated[list, add_messages]


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_history: List[ChatMessage] = []


class ChatStreamRequest(BaseModel):
    message: str
    conversation_history: List[ChatMessage] = []
    stream_mode: str = "messages"  # "messages", "updates", "values", "custom"


class ChatResponse(BaseModel):
    response: str
    conversation_history: List[ChatMessage]


class LangGraphChatbot:
    def __init__(self, model_name: str = MODEL):
        self.llm = init_chat_model(model_name)
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        graph_builder = StateGraph(State)
        
        graph_builder.add_node("chatbot", self._chatbot_node)
        
        graph_builder.add_edge(START, "chatbot")
        graph_builder.add_edge("chatbot", END)
        
        return graph_builder.compile()
    
    def _chatbot_node(self, state: State) -> Dict[str, Any]:
        response = self.llm.invoke(state["messages"])
        return {"messages": [response]}
    
    def _convert_to_langchain_messages(self, messages: List[ChatMessage]) -> List:
        langchain_messages = []
        for msg in messages:
            if msg.role == "user":
                langchain_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                langchain_messages.append(AIMessage(content=msg.content))
        return langchain_messages
    
    def _convert_from_langchain_messages(self, messages: List) -> List[ChatMessage]:
        chat_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                chat_messages.append(ChatMessage(role="user", content=msg.content))
            elif isinstance(msg, AIMessage):
                chat_messages.append(ChatMessage(role="assistant", content=msg.content))
        return chat_messages
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        langchain_messages = self._convert_to_langchain_messages(request.conversation_history)
        langchain_messages.append(HumanMessage(content=request.message))
        
        initial_state = {"messages": langchain_messages}
        
        result = await self.graph.ainvoke(initial_state)
        
        all_messages = result["messages"]
        
        updated_conversation = self._convert_from_langchain_messages(all_messages)
        
        bot_response = updated_conversation[-1].content
        
        return ChatResponse(
            response=bot_response,
            conversation_history=updated_conversation
        )
    
    async def stream_chat(self, request: ChatStreamRequest) -> AsyncIterator[str]:
        langchain_messages = self._convert_to_langchain_messages(request.conversation_history)
        langchain_messages.append(HumanMessage(content=request.message))
        
        initial_state = {"messages": langchain_messages}
        
        if request.stream_mode == "messages":
            async for message_chunk, _ in self.graph.astream(
                initial_state, 
                stream_mode="messages"
            ):
                if hasattr(message_chunk, 'content') and message_chunk.content:
                    yield f"data: {json.dumps({'type': 'token', 'content': message_chunk.content})}\n\n"
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
        elif request.stream_mode == "updates":
                # Stream node updates
                async for chunk in self.graph.astream(
                    initial_state, 
                    stream_mode="updates"
                ):
                    # Serialize the chunk to handle non-JSON serializable objects
                    serialized_chunk = self._serialize_chunk(chunk)
                    chunk_data = {
                        "type": "update",
                        "content": serialized_chunk
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
        elif request.stream_mode == "values":
                # Stream full state values
                async for chunk in self.graph.astream(
                    initial_state, 
                    stream_mode="values"
                ):
                    # Convert messages to serializable format
                    serializable_chunk = self._serialize_state_for_streaming(chunk)
                    chunk_data = {
                        "type": "values",
                        "content": serializable_chunk
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
        else:
            raise ValueError(f"Unsupported stream mode: {request.stream_mode}")
    
    def _serialize_state_for_streaming(self, state: Dict[str, Any]) -> Dict[str, Any]:
        serialized = {}
        for key, value in state.items():
            if key == "messages":
                serialized[key] = [
                    {
                        "type": type(msg).__name__,
                        "content": getattr(msg, 'content', str(msg))
                    }
                    for msg in value
                ]
            else:
                serialized[key] = value
        return serialized
    
    def _serialize_chunk(self, chunk: Any) -> Dict[str, Any]:
        """
        Serialize any chunk data to JSON-safe format.
        
        Args:
            chunk: The chunk to serialize (can contain LangChain objects)
            
        Returns:
            JSON-serializable dictionary
        """
        if isinstance(chunk, dict):
            serialized = {}
            for key, value in chunk.items():
                serialized[key] = self._serialize_value(value)
            return serialized
        else:
            return self._serialize_value(chunk)
    
    def _serialize_value(self, value: Any) -> Any:
        """
        Serialize a single value to JSON-safe format.
        
        Args:
            value: The value to serialize
            
        Returns:
            JSON-serializable value
        """
        # Handle None
        if value is None:
            return None
            
        # Handle basic JSON-serializable types
        elif isinstance(value, (str, int, float, bool)):
            return value
            
        # Handle LangChain messages
        elif hasattr(value, '__class__') and 'Message' in value.__class__.__name__:
            return {
                "type": value.__class__.__name__,
                "content": getattr(value, 'content', ''),
                "role": getattr(value, 'type', 'unknown'),
                "additional_kwargs": getattr(value, 'additional_kwargs', {}),
                "id": getattr(value, 'id', None)
            }
            
        # Handle lists
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(item) for item in value]
            
        # Handle dictionaries
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
            
        # Handle sets
        elif isinstance(value, set):
            return list(value)
            
        # Handle datetime objects
        elif hasattr(value, 'isoformat'):
            return value.isoformat()
            
        # Handle UUID objects
        elif hasattr(value, 'hex'):
            return str(value)
            
        # Handle objects with __dict__ (custom classes)
        elif hasattr(value, '__dict__'):
            try:
                return {
                    "type": value.__class__.__name__,
                    "data": self._serialize_value(value.__dict__)
                }
            except:
                return str(value)
                
        # Handle callable objects
        elif callable(value):
            return f"<function: {getattr(value, '__name__', str(value))}>"
            
        # Fallback: convert to string representation
        else:
            try:
                # Try to convert to string, but handle potential encoding issues
                return str(value)
            except Exception as e:
                return f"<non-serializable: {type(value).__name__}>"
    
    def chat_sync(self, request: ChatRequest) -> ChatResponse:
        langchain_messages = self._convert_to_langchain_messages(request.conversation_history)
        langchain_messages.append(HumanMessage(content=request.message))
        
        initial_state = {"messages": langchain_messages}
        
        result = self.graph.invoke(initial_state)
        
        all_messages = result["messages"]
        
        updated_conversation = self._convert_from_langchain_messages(all_messages)
        
        bot_response = updated_conversation[-1].content
        
        return ChatResponse(
            response=bot_response,
            conversation_history=updated_conversation
        )