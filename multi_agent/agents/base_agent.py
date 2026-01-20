"""
Base agent class with common functionality.
"""

from typing import Dict, Any, Optional, List, Union
from crewai import Agent
import logging
import os

logger = logging.getLogger(__name__)

# Try to import tools, but make it optional
try:
    from crewai.tools import BaseTool
    ToolType = Union[BaseTool, Any]
except ImportError:
    # BaseTool not available in this CrewAI version
    ToolType = Any


class BaseAgent:
    """Base class for all agents with common functionality."""
    
    def __init__(self, name: str, role: str, goal: str, backstory: str,
                 tools: Optional[List[ToolType]] = None,
                 model: str = "deepseek-chat",
                 temperature: float = 0.3,
                 verbose: bool = True):
        """
        Initialize base agent.
        
        Args:
            name: Agent name
            role: Agent role description
            goal: Agent goal
            backstory: Agent backstory
            tools: List of tools available to agent
            model: LLM model to use
            temperature: LLM temperature
            verbose: Enable verbose logging
        """
        self.name = name
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.tools = tools or []
        self.model = model
        self.temperature = temperature
        self.verbose = verbose
        
        # Initialize LLM tools if API keys are available
        self.llm_tools = None
        try:
            from ..tools.llm_tools import LLMTools
            self.llm_tools = LLMTools(model=model)
            if self.llm_tools.is_available():
                logger.info(f"{self.name}: LLM available ({'DeepSeek' if self.llm_tools.use_deepseek else 'Anthropic'})")
            else:
                logger.debug(f"{self.name}: LLM not available (no API key)")
        except ImportError as e:
            logger.debug(f"{self.name}: LLM tools not available: {e}")
        
        # Create CrewAI agent (optional - only if needed for CrewAI tasks)
        # Skip creation since we're using direct method calls, not CrewAI tasks
        self._crewai_agent = None
        
        # Optionally create CrewAI agent if LLM is available and user wants it
        if self.llm_tools and self.llm_tools.is_available():
            try:
                # Configure LLM for CrewAI
                if self.llm_tools.use_anthropic:
                    from langchain_anthropic import ChatAnthropic
                    llm = ChatAnthropic(
                        model=self.llm_tools.model or "claude-3-opus-20240229",
                        temperature=temperature
                    )
                elif self.llm_tools.use_deepseek:
                    # DeepSeek uses OpenAI-compatible API
                    from langchain_openai import ChatOpenAI
                    llm = ChatOpenAI(
                        model=self.llm_tools.model or "deepseek-chat",
                        temperature=temperature,
                        openai_api_key=self.llm_tools.api_key,
                        openai_api_base="https://api.deepseek.com/v1"
                    )
                else:
                    llm = None
                
                if llm:
                    self._crewai_agent = Agent(
                        role=role,
                        goal=goal,
                        backstory=backstory,
                        tools=tools or [],
                        verbose=verbose,
                        allow_delegation=False,
                        llm=llm
                    )
                    logger.debug(f"{self.name}: CrewAI Agent created with LLM")
            except Exception as e:
                logger.debug(f"{self.name}: Could not create CrewAI Agent: {e}")
    
    def process(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a task with optional context.
        
        Args:
            task_description: Description of the task
            context: Optional context dictionary
            
        Returns:
            Dictionary with agent output
        """
        try:
            # Add context to task if provided
            if context:
                task_description = f"{task_description}\n\nContext: {context}"
            
            # This will be implemented by subclasses or used with CrewAI tasks
            logger.info(f"{self.name} processing task: {task_description[:100]}...")
            
            return {
                "agent": self.name,
                "status": "completed",
                "output": {}
            }
        except Exception as e:
            logger.error(f"Error in {self.name}: {e}")
            return {
                "agent": self.name,
                "status": "error",
                "error": str(e)
            }
    
    def get_agent(self) -> Optional[Agent]:
        """Get the underlying CrewAI agent (if available)."""
        return self._crewai_agent
    
    def use_llm_analysis(self) -> bool:
        """Check if LLM analysis is available."""
        return self.llm_tools is not None and self.llm_tools.is_available()
    
    def enhance_with_llm(self, data: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
        """
        Enhance analysis results with LLM-generated insights.
        
        Args:
            data: Analysis data dictionary
            analysis_type: Type of analysis (tax, estate, investment)
            
        Returns:
            Enhanced data dictionary with LLM insights
        """
        if not self.use_llm_analysis():
            return data
        
        try:
            # Generate LLM recommendations
            llm_recommendations = self.llm_tools.generate_recommendations(data, analysis_type)
            
            # Generate explanation
            explanation = self.llm_tools.explain_analysis(data, analysis_type)
            
            # Add LLM insights to data
            enhanced = data.copy()
            enhanced['llm_insights'] = {
                'explanation': explanation,
                'recommendations': llm_recommendations,
                'llm_provider': 'DeepSeek' if self.llm_tools.use_deepseek else 'Anthropic'
            }
            
            return enhanced
        except Exception as e:
            logger.error(f"Error enhancing with LLM: {e}")
            return data

