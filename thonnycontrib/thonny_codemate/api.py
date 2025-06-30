"""
Thonny CodeMate API
Thonny上で実行するプログラムからLLMにアクセスするためのシンプルなAPI
"""
from typing import Optional, Iterator


def ask(prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> str:
    """
    LLMに質問して回答を取得
    
    Args:
        prompt: 質問や指示
        temperature: 生成の創造性（0.0-1.0）
        max_tokens: 最大トークン数
        
    Returns:
        LLMの回答
        
    Example:
        >>> from thonnycontrib.thonny_codemate.api import ask
        >>> answer = ask("Pythonでリストを逆順にする方法を教えて")
        >>> print(answer)
    """
    from . import get_llm_client
    
    try:
        client = get_llm_client()
        return client.generate(prompt, temperature=temperature, max_tokens=max_tokens)
    except Exception as e:
        return f"Error: {str(e)}"


def ask_stream(prompt: str, temperature: float = 0.7) -> Iterator[str]:
    """
    LLMに質問してストリーミングで回答を取得
    
    Args:
        prompt: 質問や指示
        temperature: 生成の創造性（0.0-1.0）
        
    Yields:
        LLMの回答をトークンごとに
        
    Example:
        >>> from thonnycontrib.thonny_codemate.api import ask_stream
        >>> for token in ask_stream("Hello, how are you?"):
        ...     print(token, end="", flush=True)
    """
    from . import get_llm_client
    
    try:
        client = get_llm_client()
        for token in client.generate_stream(prompt, temperature=temperature):
            yield token
    except Exception as e:
        yield f"Error: {str(e)}"


def is_ready() -> bool:
    """
    LLMが利用可能かチェック
    
    Returns:
        True if LLM is loaded and ready
        
    Example:
        >>> from thonnycontrib.thonny_codemate.api import is_ready
        >>> if is_ready():
        ...     print("LLM is ready!")
    """
    from . import get_llm_client
    
    try:
        client = get_llm_client()
        return client.is_loaded()
    except:
        return False


def get_model_info() -> dict:
    """
    現在のモデル情報を取得
    
    Returns:
        モデル情報の辞書
        
    Example:
        >>> from thonnycontrib.thonny_codemate.api import get_model_info
        >>> info = get_model_info()
        >>> print(f"Model: {info.get('model_path', 'Not loaded')}")
    """
    from . import get_llm_client
    from thonny import get_workbench
    
    wb = get_workbench()
    
    info = {
        "provider": wb.get_option("llm.provider", "local"),
        "model_path": wb.get_option("llm.model_path", ""),
        "context_size": wb.get_option("llm.context_size", 4096),
    }
    
    try:
        client = get_llm_client()
        info["is_loaded"] = client.is_loaded()
    except:
        info["is_loaded"] = False
    
    return info


# 簡易的なチャットクラス
class Chat:
    """
    会話履歴を保持するチャットクラス
    
    Example:
        >>> from thonnycontrib.thonny_codemate.api import Chat
        >>> chat = Chat()
        >>> response = chat.send("Pythonとは何ですか？")
        >>> print(response)
        >>> response = chat.send("もっと詳しく教えて")  # 文脈を保持
        >>> print(response)
    """
    
    def __init__(self):
        self.history = []
    
    def send(self, message: str, temperature: float = 0.7) -> str:
        """メッセージを送信して返答を取得"""
        from . import get_llm_client
        
        self.history.append({"role": "user", "content": message})
        
        try:
            client = get_llm_client()
            response = client.generate(
                message,
                messages=self.history,
                temperature=temperature
            )
            
            self.history.append({"role": "assistant", "content": response})
            return response
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.history.append({"role": "assistant", "content": error_msg})
            return error_msg
    
    def clear(self):
        """会話履歴をクリア"""
        self.history = []