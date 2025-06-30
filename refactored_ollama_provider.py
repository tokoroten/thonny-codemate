"""
Refactored OllamaProvider for both Ollama and LM Studio
Both support OpenAI compatible API
"""

class OllamaProvider(ExternalProvider):
    """Ollama/LM Studio APIプロバイダー（OpenAI互換）"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.headers = {"Content-Type": "application/json"}
        
        # OpenAI client - both Ollama and LM Studio support OpenAI compatible API
        self.openai_client = None
        if OPENAI_AVAILABLE:
            try:
                # Determine API base URL
                if base_url.endswith('/v1'):
                    api_base = base_url
                else:
                    api_base = f"{self.base_url}/v1"
                
                self.openai_client = OpenAI(
                    api_key="not-needed",  # Ollama/LM Studio don't require real API key
                    base_url=api_base
                )
                logger.info(f"Initialized OpenAI client for {base_url} with API base: {api_base}")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """テキスト生成（非ストリーミング）"""
        messages = kwargs.get("messages", [])
        if not messages:
            messages = [{"role": "user", "content": prompt}]
        
        if not self.openai_client:
            raise Exception("OpenAI library is not available. Please install it with: pip install openai")
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2048),
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Failed to generate: {e}")
            raise
    
    def generate_stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """ストリーミング生成"""
        messages = kwargs.get("messages", [])
        if not messages:
            messages = [{"role": "user", "content": prompt}]
        
        if not self.openai_client:
            raise Exception("OpenAI library is not available. Please install it with: pip install openai")
        
        try:
            stream = self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2048),
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            yield f"[Error: {str(e)}]"
    
    @retry_network_operation
    def get_models(self) -> list[str]:
        """利用可能なモデルのリストを取得"""
        try:
            if self.openai_client:
                models = self.openai_client.models.list()
                return [m.id for m in models.data]
            else:
                # Fallback: Try Ollama native API if OpenAI client not available
                req = urllib.request.Request(f"{self.base_url}/api/tags")
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    return [m['name'] for m in data.get('models', [])]
        except Exception as e:
            logger.error(f"Failed to fetch models: {e}")
            return []
    
    def get_model_info(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """モデルの詳細情報を取得"""
        model = model_name or self.model
        
        try:
            # Try OpenAI compatible endpoint first
            if self.openai_client:
                try:
                    models = self.openai_client.models.list()
                    for model_data in models.data:
                        if model_data.id == model:
                            # Extract context size from various possible fields
                            context_size = None
                            for attr in ['context_window', 'context_length', 'max_context_length']:
                                if hasattr(model_data, attr):
                                    context_size = getattr(model_data, attr)
                                    if context_size:
                                        break
                            
                            return {
                                "context_size": context_size,
                                "model_data": model_data.model_dump() if hasattr(model_data, 'model_dump') else model_data
                            }
                except Exception as e:
                    logger.debug(f"OpenAI API model info failed, trying native API: {e}")
            
            # Fallback: Ollama native API
            data = {"name": model}
            req = urllib.request.Request(
                f"{self.base_url}/api/show",
                data=json.dumps(data).encode('utf-8'),
                headers=self.headers
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                # Extract context size from parameters
                parameters = result.get('parameters', '')
                context_size = 2048  # default
                
                if parameters:
                    import re
                    match = re.search(r'num_ctx\s+(\d+)', parameters)
                    if match:
                        context_size = int(match.group(1))
                
                return {
                    "context_size": context_size,
                    "model_data": result
                }
                
        except Exception as e:
            logger.error(f"Failed to get model info for {model}: {e}")
            return {"context_size": None, "error": str(e)}
    
    def test_connection(self) -> Dict[str, Any]:
        """接続テスト"""
        try:
            # Get available models
            models = self.get_models()
            
            if not models:
                return {
                    "success": False,
                    "provider": "Ollama/LM Studio",
                    "base_url": self.base_url,
                    "error": "No models found"
                }
            
            # Try a simple completion
            test_model = self.model if self.model in models else models[0]
            
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=test_model,
                    messages=[{"role": "user", "content": "Say 'Hello' in one word."}],
                    max_tokens=10
                )
                response_text = response.choices[0].message.content
            else:
                response_text = self.generate("Say 'Hello' in one word.", max_tokens=10)
            
            return {
                "success": True,
                "provider": "Ollama/LM Studio",
                "base_url": self.base_url,
                "model": test_model,
                "available_models": models,
                "response": response_text
            }
        except Exception as e:
            return {
                "success": False,
                "provider": "Ollama/LM Studio",
                "base_url": self.base_url,
                "model": self.model,
                "error": str(e)
            }