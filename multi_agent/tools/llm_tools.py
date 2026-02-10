"""
LLM tools for agent reasoning and analysis.
Supports Anthropic Claude and DeepSeek APIs.
"""

import os
import time
import logging
from typing import Dict, Any, Optional, List
import json

logger = logging.getLogger(__name__)


def _record_llm_span(provider: str, model: str, prompt_preview: str, response_preview: str, duration_ms: float, error: Optional[str] = None) -> None:
    """Record LLM call to observability if context is set."""
    try:
        from ..observability.hooks import record_llm_call, get_current_context
        session_id, parent_span_id = get_current_context()
        if session_id:
            record_llm_call(
                provider=provider,
                model=model,
                prompt_preview=prompt_preview,
                response_preview=response_preview,
                duration_ms=duration_ms,
                session_id=session_id,
                parent_span_id=parent_span_id,
                error=error,
            )
    except Exception:
        pass


class LLMTools:
    """Tools for LLM-based reasoning and analysis."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize LLM tools.
        
        Args:
            api_key: Optional API key (if None, uses environment variables)
            model: Optional model name (if None, auto-detects based on available API keys)
        """
        self.model = model
        self.api_key = api_key
        
        # Check environment variables (priority: DeepSeek > Anthropic)
        deepseek_key = os.getenv('DEEPSEEK_API_KEY')
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        
        # Determine which API to use
        if api_key:
            self.api_key = api_key
            # Try to infer provider from key format or model name
            if model and 'deepseek' in model.lower():
                self.use_deepseek = True
                self.use_anthropic = False
            elif model and 'claude' in model.lower():
                self.use_deepseek = False
                self.use_anthropic = True
            else:
                # Default to DeepSeek if key format matches
                self.use_deepseek = bool(deepseek_key or (api_key and 'sk-' in str(api_key)))
                self.use_anthropic = bool(anthropic_key and not self.use_deepseek)
        else:
            self.use_deepseek = bool(deepseek_key)
            self.use_anthropic = bool(anthropic_key and not self.use_deepseek)
            self.api_key = deepseek_key or anthropic_key
        
        # Set default model if not specified
        if not self.model:
            if self.use_deepseek:
                self.model = "deepseek-chat"
            elif self.use_anthropic:
                self.model = "claude-3-opus-20240229"
            else:
                self.model = None
        
        self._llm_available = bool(self.api_key)
    
    def is_available(self) -> bool:
        """Check if LLM is available."""
        return self._llm_available
    
    def analyze_with_llm(self, prompt: str, system_prompt: Optional[str] = None,
                        temperature: float = 0.3, max_tokens: int = 2000) -> Optional[str]:
        """
        Analyze a prompt using LLM.
        
        Args:
            prompt: User prompt/question
            system_prompt: Optional system prompt
            temperature: LLM temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            LLM response text or None if unavailable
        """
        if not self._llm_available:
            logger.warning("LLM not available - no API key configured")
            return None

        provider = "DeepSeek" if self.use_deepseek else "Anthropic"
        model_name = self.model or "unknown"
        prompt_preview = (prompt[:500] + "…") if len(prompt) > 500 else prompt
        start = time.perf_counter()
        err: Optional[str] = None
        response_text: Optional[str] = None
        try:
            if self.use_deepseek:
                response_text = self._call_deepseek(prompt, system_prompt, temperature, max_tokens)
            elif self.use_anthropic:
                response_text = self._call_anthropic(prompt, system_prompt, temperature, max_tokens)
            else:
                logger.warning("No LLM provider configured")
                return None
        except Exception as e:
            err = str(e)
            logger.error(f"Error calling LLM: {e}")
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            response_preview = (response_text[:500] + "…") if response_text and len(response_text) > 500 else (response_text or "")
            _record_llm_span(provider, model_name, prompt_preview, response_preview, duration_ms, error=err)

        return response_text
    
    def _call_deepseek(self, prompt: str, system_prompt: Optional[str],
                      temperature: float, max_tokens: int) -> str:
        """Call DeepSeek API."""
        try:
            import openai
            
            client = openai.OpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com/v1"
            )
            
            model_name = self.model if 'deepseek' in self.model.lower() else 'deepseek-chat'
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content.strip()
        except ImportError:
            logger.error("OpenAI library not installed. Install with: pip install openai")
            return None
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            raise
    
    def _call_anthropic(self, prompt: str, system_prompt: Optional[str],
                       temperature: float, max_tokens: int) -> str:
        """Call Anthropic API."""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=self.api_key)
            
            model_name = self.model if 'claude' in self.model.lower() else 'claude-3-opus-20240229'
            
            # Anthropic uses different message format
            messages = [{"role": "user", "content": prompt}]
            
            kwargs = {
                "model": model_name,
                "max_tokens": max_tokens,
                "messages": messages
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            response = client.messages.create(**kwargs)
            
            return response.content[0].text.strip()
        except ImportError:
            logger.error("Anthropic library not installed. Install with: pip install anthropic")
            return None
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    def generate_recommendations(self, context: Dict[str, Any], 
                                 recommendation_type: str = "general") -> List[Dict[str, Any]]:
        """
        Generate recommendations using LLM based on context.
        
        Args:
            context: Context dictionary with data
            recommendation_type: Type of recommendations (tax, estate, investment)
            
        Returns:
            List of recommendation dictionaries
        """
        if not self._llm_available:
            return []
        
        system_prompts = {
            "tax": """You are a Canadian tax expert. Analyze the portfolio data and provide
            tax optimization recommendations. Focus on capital gains, tax-loss harvesting,
            and account type optimization. Be specific and actionable.""",
            
            "estate": """You are an estate planning expert. Analyze the portfolio structure
            and provide estate planning recommendations. Focus on probate minimization,
            beneficiary designations, and product recommendations. Be specific and actionable.""",
            
            "investment": """You are an investment analyst. Analyze the portfolio holdings
            and provide investment recommendations. Focus on diversification, risk management,
            and rebalancing opportunities. Be specific and actionable.""",
            
            "general": """You are a financial advisor. Analyze the portfolio data and provide
            comprehensive financial recommendations. Be specific and actionable."""
        }
        
        system_prompt = system_prompts.get(recommendation_type, system_prompts["general"])
        
        prompt = f"""Analyze the following portfolio data and provide recommendations:

{json.dumps(context, indent=2)}

Provide your analysis and recommendations in JSON format with the following structure:
{{
    "summary": "Brief summary of findings",
    "recommendations": [
        {{
            "priority": "High/Medium/Low",
            "action": "Specific action to take",
            "rationale": "Why this recommendation",
            "impact": "Expected impact or benefit"
        }}
    ]
}}
"""
        
        response = self.analyze_with_llm(prompt, system_prompt, temperature=0.3)
        
        if not response:
            return []
        
        # Try to extract JSON from response
        try:
            # Look for JSON in the response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                result = json.loads(json_str)
                return result.get('recommendations', [])
        except json.JSONDecodeError:
            logger.warning("Could not parse LLM response as JSON")
        
        return []
    
    def explain_analysis(self, data: Dict[str, Any], analysis_type: str) -> str:
        """
        Generate a natural language explanation of analysis results.
        
        Args:
            data: Analysis data dictionary
            analysis_type: Type of analysis (tax, estate, investment)
            
        Returns:
            Natural language explanation
        """
        if not self._llm_available:
            return "LLM not available for explanation."
        
        prompt = f"""Explain the following {analysis_type} analysis results in clear,
        understandable language for a client:

{json.dumps(data, indent=2)}

Provide a clear, concise explanation that highlights key findings and actionable insights.
"""
        
        system_prompt = f"You are a financial advisor explaining {analysis_type} analysis to a client."
        
        response = self.analyze_with_llm(prompt, system_prompt, temperature=0.5)
        return response or "Could not generate explanation."

