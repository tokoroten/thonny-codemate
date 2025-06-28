"""
国際化（i18n）サポート
英語、日本語、中国語（簡体字・繁体字）をサポート
"""
from typing import Dict
from thonny import get_workbench


# 翻訳辞書
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # 日本語
    "ja": {
        # UI要素
        "LLM Assistant": "LLMアシスタント",
        "Show LLM Assistant": "LLMアシスタントを表示",
        "Explain Selected Code": "選択したコードを説明",
        "Generate Code from Comment": "コメントからコードを生成",
        "AI: Explain Selected Code": "AI: 選択したコードを説明",
        "AI: Generate Code from Comment": "AI: コメントからコードを生成",
        "Clear": "クリア",
        "Send": "送信",
        "Stop": "停止",
        "Stopping...": "停止中...",
        "Ctrl+Enter to send": "Ctrl+Enterで送信",
        "Explain Error": "エラーを説明",
        "Include Context": "コンテキストを含める",
        "Settings": "設定",
        
        # 設定ダイアログ
        "LLM Assistant Settings": "LLMアシスタント設定",
        "Model Settings": "モデル設定",
        "Model Path:": "モデルパス:",
        "Browse...": "参照...",
        "Context Size:": "コンテキストサイズ:",
        "Generation Settings": "生成設定",
        "Temperature:": "Temperature:",
        "Max Tokens:": "最大トークン数:",
        "User Settings": "ユーザー設定",
        "Skill Level:": "スキルレベル:",
        "Use Markdown View:": "Markdownビューを使用:",
        "Enable Markdown rendering (requires tkinterweb)": "Markdownレンダリングを有効化（tkinterwebが必要）",
        "Output Language:": "出力言語:",
        "Auto (Follow Thonny)": "自動（Thonnyに従う）",
        "Language code:": "言語コード:",
        "Provider Settings": "プロバイダー設定",
        "Provider:": "プロバイダー:",
        "API Key:": "APIキー:",
        "Base URL:": "ベースURL:",
        "Model Name:": "モデル名:",
        "System Prompt": "システムプロンプト",
        "Prompt Type:": "プロンプトタイプ:",
        "Default": "デフォルト",
        "Custom": "カスタム",
        "Edit Custom Prompt": "カスタムプロンプトを編集",
        "Save": "保存",
        "Cancel": "キャンセル",
        "Test Model": "モデルをテスト",
        "Download Models": "モデルをダウンロード",
        
        # モデルダウンロードダイアログ
        "Model Manager": "モデルマネージャー",
        "Recommended Models": "推奨モデル",
        "Refresh": "更新",
        "Size:": "サイズ:",
        "Languages:": "言語:",
        "Installed": "インストール済み",
        "Use This Model": "このモデルを使用",
        "Delete": "削除",
        "Downloading...": "ダウンロード中...",
        "Not installed": "未インストール",
        "Download": "ダウンロード",
        
        # メッセージ
        "Loading": "読み込み中",
        "Ready": "準備完了",
        "No model loaded": "モデルが読み込まれていません",
        "Load failed": "読み込み失敗",
        "Previous conversation restored": "前回の会話を復元しました",
        "Context enabled for selected text": "選択テキストのコンテキストを有効化",
        "Context enabled for current file": "現在のファイルのコンテキストを有効化",
        "Context enabled but no file is currently open": "コンテキストは有効ですが、開いているファイルがありません",
        "Context disabled": "コンテキスト無効",
        "[Generation stopped by user]": "[ユーザーによって生成が停止されました]",
        "Error": "エラー",
        "Success": "成功",
        "Failed to load model:": "モデルの読み込みに失敗:",
        "No model found. Please download a model from Settings → Download Models.": "モデルが見つかりません。設定→モデルをダウンロードからモデルをダウンロードしてください。",
        "Model downloaded successfully!": "モデルのダウンロードが完了しました！",
        "Failed to download": "ダウンロードに失敗しました",
        
        # スキルレベル
        "beginner": "初心者",
        "intermediate": "中級者",
        "advanced": "上級者",
    },
    
    # 簡体字中国語
    "zh_CN": {
        # UI要素
        "LLM Assistant": "LLM助手",
        "Show LLM Assistant": "显示LLM助手",
        "Explain Selected Code": "解释选中的代码",
        "Generate Code from Comment": "从注释生成代码",
        "AI: Explain Selected Code": "AI: 解释选中的代码",
        "AI: Generate Code from Comment": "AI: 从注释生成代码",
        "Clear": "清除",
        "Send": "发送",
        "Stop": "停止",
        "Stopping...": "正在停止...",
        "Ctrl+Enter to send": "按Ctrl+Enter发送",
        "Explain Error": "解释错误",
        "Include Context": "包含上下文",
        "Settings": "设置",
        
        # 設定ダイアログ
        "LLM Assistant Settings": "LLM助手设置",
        "Model Settings": "模型设置",
        "Model Path:": "模型路径:",
        "Browse...": "浏览...",
        "Context Size:": "上下文大小:",
        "Generation Settings": "生成设置",
        "Temperature:": "温度:",
        "Max Tokens:": "最大令牌数:",
        "User Settings": "用户设置",
        "Skill Level:": "技能水平:",
        "Use Markdown View:": "使用Markdown视图:",
        "Enable Markdown rendering (requires tkinterweb)": "启用Markdown渲染（需要tkinterweb）",
        "Output Language:": "输出语言:",
        "Auto (Follow Thonny)": "自动（跟随Thonny）",
        "Language code:": "语言代码:",
        "Provider Settings": "提供商设置",
        "Provider:": "提供商:",
        "API Key:": "API密钥:",
        "Base URL:": "基础URL:",
        "Model Name:": "模型名称:",
        "System Prompt": "系统提示",
        "Prompt Type:": "提示类型:",
        "Default": "默认",
        "Custom": "自定义",
        "Edit Custom Prompt": "编辑自定义提示",
        "Save": "保存",
        "Cancel": "取消",
        "Test Model": "测试模型",
        "Download Models": "下载模型",
        
        # モデルダウンロードダイアログ
        "Model Manager": "模型管理器",
        "Recommended Models": "推荐模型",
        "Refresh": "刷新",
        "Size:": "大小:",
        "Languages:": "语言:",
        "Installed": "已安装",
        "Use This Model": "使用此模型",
        "Delete": "删除",
        "Downloading...": "正在下载...",
        "Not installed": "未安装",
        "Download": "下载",
        
        # メッセージ
        "Loading": "正在加载",
        "Ready": "就绪",
        "No model loaded": "未加载模型",
        "Load failed": "加载失败",
        "Previous conversation restored": "已恢复上次对话",
        "Context enabled for selected text": "已为选定文本启用上下文",
        "Context enabled for current file": "已为当前文件启用上下文",
        "Context enabled but no file is currently open": "上下文已启用但当前没有打开的文件",
        "Context disabled": "上下文已禁用",
        "[Generation stopped by user]": "[用户已停止生成]",
        "Error": "错误",
        "Success": "成功",
        "Failed to load model:": "加载模型失败:",
        "No model found. Please download a model from Settings → Download Models.": "未找到模型。请从设置→下载模型中下载模型。",
        "Model downloaded successfully!": "模型下载成功！",
        "Failed to download": "下载失败",
        
        # スキルレベル
        "beginner": "初学者",
        "intermediate": "中级",
        "advanced": "高级",
    },
    
    # 繁体字中国語
    "zh_TW": {
        # UI要素
        "LLM Assistant": "LLM助手",
        "Show LLM Assistant": "顯示LLM助手",
        "Explain Selected Code": "解釋選取的程式碼",
        "Generate Code from Comment": "從註解生成程式碼",
        "AI: Explain Selected Code": "AI: 解釋選取的程式碼",
        "AI: Generate Code from Comment": "AI: 從註解生成程式碼",
        "Clear": "清除",
        "Send": "發送",
        "Stop": "停止",
        "Stopping...": "正在停止...",
        "Ctrl+Enter to send": "按Ctrl+Enter發送",
        "Explain Error": "解釋錯誤",
        "Include Context": "包含上下文",
        "Settings": "設定",
        
        # 設定ダイアログ
        "LLM Assistant Settings": "LLM助手設定",
        "Model Settings": "模型設定",
        "Model Path:": "模型路徑:",
        "Browse...": "瀏覽...",
        "Context Size:": "上下文大小:",
        "Generation Settings": "生成設定",
        "Temperature:": "溫度:",
        "Max Tokens:": "最大令牌數:",
        "User Settings": "使用者設定",
        "Skill Level:": "技能水準:",
        "Use Markdown View:": "使用Markdown檢視:",
        "Enable Markdown rendering (requires tkinterweb)": "啟用Markdown渲染（需要tkinterweb）",
        "Output Language:": "輸出語言:",
        "Auto (Follow Thonny)": "自動（跟隨Thonny）",
        "Language code:": "語言代碼:",
        "Provider Settings": "提供商設定",
        "Provider:": "提供商:",
        "API Key:": "API金鑰:",
        "Base URL:": "基礎URL:",
        "Model Name:": "模型名稱:",
        "System Prompt": "系統提示",
        "Prompt Type:": "提示類型:",
        "Default": "預設",
        "Custom": "自訂",
        "Edit Custom Prompt": "編輯自訂提示",
        "Save": "儲存",
        "Cancel": "取消",
        "Test Model": "測試模型",
        "Download Models": "下載模型",
        
        # モデルダウンロードダイアログ
        "Model Manager": "模型管理器",
        "Recommended Models": "推薦模型",
        "Refresh": "重新整理",
        "Size:": "大小:",
        "Languages:": "語言:",
        "Installed": "已安裝",
        "Use This Model": "使用此模型",
        "Delete": "刪除",
        "Downloading...": "正在下載...",
        "Not installed": "未安裝",
        "Download": "下載",
        
        # メッセージ
        "Loading": "正在載入",
        "Ready": "就緒",
        "No model loaded": "未載入模型",
        "Load failed": "載入失敗",
        "Previous conversation restored": "已還原上次對話",
        "Context enabled for selected text": "已為選取文字啟用上下文",
        "Context enabled for current file": "已為目前檔案啟用上下文",
        "Context enabled but no file is currently open": "上下文已啟用但目前沒有開啟的檔案",
        "Context disabled": "上下文已停用",
        "[Generation stopped by user]": "[使用者已停止生成]",
        "Error": "錯誤",
        "Success": "成功",
        "Failed to load model:": "載入模型失敗:",
        "No model found. Please download a model from Settings → Download Models.": "未找到模型。請從設定→下載模型中下載模型。",
        "Model downloaded successfully!": "模型下載成功！",
        "Failed to download": "下載失敗",
        
        # スキルレベル
        "beginner": "初學者",
        "intermediate": "中級",
        "advanced": "高級",
    }
}


def get_current_language() -> str:
    """現在の言語コードを取得（英語にフォールバック）"""
    try:
        workbench = get_workbench()
        lang = workbench.get_option("general.language", "en_US")
        
        # 言語コードを正規化
        if lang.startswith("ja"):
            return "ja"
        elif lang.startswith("zh"):
            if "TW" in lang or "HK" in lang:
                return "zh_TW"
            else:
                return "zh_CN"
        else:
            # その他の言語は英語にフォールバック
            return "en"
    except:
        return "en"


def tr(text: str) -> str:
    """
    テキストを翻訳（Translation）
    
    Args:
        text: 翻訳するテキスト
        
    Returns:
        翻訳されたテキスト（見つからない場合は元のテキスト）
    """
    lang = get_current_language()
    
    # 英語の場合はそのまま返す
    if lang == "en":
        return text
    
    # 翻訳辞書から取得
    if lang in TRANSLATIONS and text in TRANSLATIONS[lang]:
        return TRANSLATIONS[lang][text]
    
    # 見つからない場合は元のテキストを返す
    return text