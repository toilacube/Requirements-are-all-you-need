from langchain_core.tools import tool
from langchain_tavily import TavilySearch

@tool
def requirements_gathering():
    
    pass


search_tool = TavilySearch(max_results=1)