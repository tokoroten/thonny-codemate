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
        "Temperature:": "温度（創造性）:",
        "Max Tokens:": "出力最大トークン数:",
        "User Settings": "ユーザー設定",
        "Skill Level:": "スキルレベル:",
        "Use Markdown View:": "Markdownビューを使用:",
        "Enable Markdown rendering (requires tkinterweb)": "Markdownレンダリングを有効化（tkinterwebが必要）",
        "Output Language:": "出力言語:",
        "Auto (Follow Thonny)": "自動（Thonnyに従う）",
        "Language code:": "言語コード:",
        "Provider Settings": "プロバイダー設定",
        "Provider:": "LLMプロバイダー:",
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
        "Test": "テスト",
        "Download Models": "モデルをダウンロード",
        "Test Connection": "接続テスト",
        "Basic Settings": "基本設定",
        "Advanced Settings": "詳細設定",
        "Repeat Penalty:": "繰り返しペナルティ:",
        
        
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
        "Please select a valid model file!": "有効なモデルファイルを選択してください！",
        "Model file found!": "モデルファイルが見つかりました！",
        "API key is required for {}": "{}にはAPIキーが必要です",
        "Testing {} connection...": "{}への接続をテスト中...",
        "Model file does not exist!": "モデルファイルが存在しません！",
        "LLM Busy": "LLM実行中",
        "Please wait for the current generation to complete.": "現在の生成が完了するまでお待ちください。",
        "Generating...": "生成中...",
        "Loading...": "読み込み中...",
        "Testing...": "テスト中...",
        "No Models": "モデルなし",
        "No models found in Ollama. Please pull a model first using 'ollama pull <model>'": "Ollamaにモデルが見つかりません。まず 'ollama pull <model>' でモデルをダウンロードしてください。",
        "Failed to connect to Ollama: {}": "Ollama/LM Studioへの接続に失敗しました: {}",
        "Failed to fetch models: {}": "モデルの取得に失敗しました: {}",
        "Server:": "サーバー:",
        "Host:": "ホスト:",
        "Port:": "ポート:",
        "(File not found)": "(ファイルが見つかりません)",
        "Presets:": "プリセット:",
        "No Editor": "エディタなし",
        "Please open a file in the editor first.": "まずエディタでファイルを開いてください。",
        "Code inserted into editor!": "コードをエディタに挿入しました！",
        "Connected to {} API. Ready to chat!": "{} APIに接続しました。チャット準備完了！",
        "LLM model loaded successfully!": "LLMモデルの読み込みに成功しました！",
        "tkinterweb is not installed": "tkinterwebがインストールされていません",
        "To enable Markdown rendering and interactive features,\nplease install tkinterweb:\n\npip install tkinterweb": "Markdownレンダリングと対話機能を有効にするには、\ntkinterwebをインストールしてください：\n\npip install tkinterweb",
        
        # エラーメッセージ
        "File not found during {}: {}": "{}中にファイルが見つかりません: {}",
        "Permission denied during {}: {}": "{}中にアクセスが拒否されました: {}",
        "Connection failed during {}: {}": "{}中に接続に失敗しました: {}",
        "Operation timed out during {}: {}": "{}中にタイムアウトしました: {}",
        "Invalid value during {}: {}": "{}中に無効な値です: {}",
        "Missing dependency during {}: {}": "{}中に依存関係が不足しています: {}",
        "Error during {}: {}": "{}中にエラーが発生しました: {}",
        "Connection failed. Please check your internet connection or server settings.": "接続に失敗しました。インターネット接続またはサーバー設定を確認してください。",
        "Request timed out. Please try again.": "リクエストがタイムアウトしました。もう一度お試しください。",
        "API key error. Please check your API key in settings.": "APIキーエラー。設定でAPIキーを確認してください。",
        "Model error. Please check if the model is properly loaded.": "モデルエラー。モデルが正しく読み込まれているか確認してください。",
        "LLM module not installed. Please install llama-cpp-python.": "LLMモジュールがインストールされていません。llama-cpp-pythonをインストールしてください。",
        "Failed to initialize LLM": "LLMの初期化に失敗しました",
        
        # スキルレベル
        "beginner": "初心者",
        "intermediate": "中級者",
        "advanced": "上級者",
        
        # カスタムプロンプトダイアログ
        "Edit Custom System Prompt": "カスタムシステムプロンプトを編集",
        "Enter your custom system prompt. This will be used to instruct the AI on how to respond.": "カスタムシステムプロンプトを入力してください。これはAIの応答方法を指示するために使用されます。",
        "Tips": "ヒント",
        "• Use {skill_level} to reference the user's skill level": "• {skill_level} でユーザーのスキルレベルを参照",
        "• Use {language} to reference the output language": "• {language} で出力言語を参照",
        "• Be specific about the coding style and explanation depth": "• コーディングスタイルと説明の深さを具体的に指定",
        "• Include examples of how you want the AI to respond": "• AIにどのように応答してほしいかの例を含める",
        "Presets:": "プリセット:",
        "Educational": "教育用",
        "Professional": "プロフェッショナル",
        "Minimal": "最小限",
        "Variables: {skill_level} = 'beginner/intermediate/advanced (with detailed description)', {language} = 'ja/en/zh-CN/zh-TW/auto'": "変数: {skill_level} = '初心者/中級者/上級者（詳細説明付き）', {language} = 'ja/en/zh-CN/zh-TW/auto'",
        "Controls randomness: 0.0 = deterministic, 2.0 = very creative": "ランダム性を制御: 0.0 = 決定的, 2.0 = 非常に創造的",
        "Maximum number of tokens the model can process at once": "モデルが一度に処理できる最大トークン数（記憶の大きさ）。大きいほどメモリ消費量が増え、生成速度が遅くなります",
        "Maximum number of tokens the model will generate in one response": "モデルが1回の応答で生成する最大トークン数",
        "Penalty for repeating tokens: 1.0 = no penalty, 2.0 = strong penalty": "トークン繰り返しのペナルティ: 1.0 = ペナルティなし, 2.0 = 強いペナルティ",
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
        "Temperature:": "温度（创造性）:",
        "Max Tokens:": "输出最大令牌数:",
        "User Settings": "用户设置",
        "Skill Level:": "技能水平:",
        "Use Markdown View:": "使用Markdown视图:",
        "Enable Markdown rendering (requires tkinterweb)": "启用Markdown渲染（需要tkinterweb）",
        "Output Language:": "输出语言:",
        "Auto (Follow Thonny)": "自动（跟随Thonny）",
        "Language code:": "语言代码:",
        "Provider Settings": "提供商设置",
        "Provider:": "LLM提供商:",
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
        "Test": "测试",
        "Download Models": "下载模型",
        "Test Connection": "测试连接",
        "Basic Settings": "基本设置",
        "Advanced Settings": "高级设置",
        "Repeat Penalty:": "重复惩罚:",
        
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
        "Please select a valid model file!": "请选择有效的模型文件！",
        "Model file found!": "找到模型文件！",
        "API key is required for {}": "{}需要API密钥",
        "Testing {} connection...": "正在测试{}连接...",
        "Model file does not exist!": "模型文件不存在！",
        "LLM Busy": "LLM正在执行",
        "Please wait for the current generation to complete.": "请等待当前生成完成。",
        "Generating...": "正在生成...",
        "Loading...": "正在加载...",
        "Testing...": "正在测试...",
        "No Models": "没有模型",
        "No models found in Ollama. Please pull a model first using 'ollama pull <model>'": "在Ollama中未找到模型。请先使用 'ollama pull <model>' 下载模型。",
        "Failed to connect to Ollama: {}": "连接到Ollama/LM Studio失败: {}",
        "Failed to fetch models: {}": "获取模型失败: {}",
        "Server:": "服务器:",
        "Host:": "主机:",
        "Port:": "端口:",
        "(File not found)": "(文件未找到)",
        "Presets:": "预设:",
        "No Editor": "无编辑器",
        "Please open a file in the editor first.": "请先在编辑器中打开文件。",
        "Code inserted into editor!": "代码已插入编辑器！",
        "Connected to {} API. Ready to chat!": "已连接到 {} API。准备聊天！",
        "LLM model loaded successfully!": "LLM模型加载成功！",
        "tkinterweb is not installed": "未安装tkinterweb",
        "To enable Markdown rendering and interactive features,\nplease install tkinterweb:\n\npip install tkinterweb": "要启用Markdown渲染和交互功能，\n请安装tkinterweb：\n\npip install tkinterweb",
        
        # 错误消息
        "File not found during {}: {}": "{}时未找到文件: {}",
        "Permission denied during {}: {}": "{}时访问被拒绝: {}",
        "Connection failed during {}: {}": "{}时连接失败: {}",
        "Operation timed out during {}: {}": "{}时操作超时: {}",
        "Invalid value during {}: {}": "{}时值无效: {}",
        "Missing dependency during {}: {}": "{}时缺少依赖项: {}",
        "Error during {}: {}": "{}时发生错误: {}",
        "Connection failed. Please check your internet connection or server settings.": "连接失败。请检查您的互联网连接或服务器设置。",
        "Request timed out. Please try again.": "请求超时。请重试。",
        "API key error. Please check your API key in settings.": "API密钥错误。请在设置中检查您的API密钥。",
        "Model error. Please check if the model is properly loaded.": "模型错误。请检查模型是否正确加载。",
        "LLM module not installed. Please install llama-cpp-python.": "未安装LLM模块。请安装llama-cpp-python。",
        "Failed to initialize LLM": "LLM初始化失败",
        
        # スキルレベル
        "beginner": "初学者",
        "intermediate": "中级",
        "advanced": "高级",
        
        # 自定义提示词对话框
        "Edit Custom System Prompt": "编辑自定义系统提示",
        "Enter your custom system prompt. This will be used to instruct the AI on how to respond.": "输入您的自定义系统提示。这将用于指导AI如何回应。",
        "Tips": "提示",
        "• Use {skill_level} to reference the user's skill level": "• 使用 {skill_level} 引用用户的技能水平",
        "• Use {language} to reference the output language": "• 使用 {language} 引用输出语言",
        "• Be specific about the coding style and explanation depth": "• 明确指定编码风格和解释深度",
        "• Include examples of how you want the AI to respond": "• 包含您希望AI如何回应的示例",
        "Presets:": "预设:",
        "Educational": "教育用途",
        "Professional": "专业",
        "Minimal": "最小化",
        "Variables: {skill_level} = 'beginner/intermediate/advanced (with detailed description)', {language} = 'ja/en/zh-CN/zh-TW/auto'": "变量: {skill_level} = '初学者/中级/高级（含详细描述）', {language} = 'ja/en/zh-CN/zh-TW/auto'",
        "Controls randomness: 0.0 = deterministic, 2.0 = very creative": "控制随机性: 0.0 = 确定性, 2.0 = 非常有创意",
        "Maximum number of tokens the model can process at once": "模型一次可以处理的最大令牌数（记忆大小）。越大内存消耗越多，生成速度越慢",
        "Maximum number of tokens the model will generate in one response": "模型在一次响应中生成的最大令牌数",
        "Penalty for repeating tokens: 1.0 = no penalty, 2.0 = strong penalty": "重复令牌的惩罚: 1.0 = 无惩罚, 2.0 = 强惩罚",
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
        "Temperature:": "溫度（創造性）:",
        "Max Tokens:": "輸出最大令牌數:",
        "User Settings": "使用者設定",
        "Skill Level:": "技能水準:",
        "Use Markdown View:": "使用Markdown檢視:",
        "Enable Markdown rendering (requires tkinterweb)": "啟用Markdown渲染（需要tkinterweb）",
        "Output Language:": "輸出語言:",
        "Auto (Follow Thonny)": "自動（跟隨Thonny）",
        "Language code:": "語言代碼:",
        "Provider Settings": "提供商設定",
        "Provider:": "LLM提供商:",
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
        "Test": "測試",
        "Download Models": "下載模型",
        "Test Connection": "測試連接",
        "Basic Settings": "基本設定",
        "Advanced Settings": "進階設定",
        "Repeat Penalty:": "重複懲罰:",
        
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
        "Please select a valid model file!": "請選擇有效的模型檔案！",
        "Model file found!": "找到模型檔案！",
        "API key is required for {}": "{}需要API金鑰",
        "Testing {} connection...": "正在測試{}連接...",
        "Model file does not exist!": "模型檔案不存在！",
        "LLM Busy": "LLM正在執行",
        "Please wait for the current generation to complete.": "請等待當前生成完成。",
        "Generating...": "正在生成...",
        "Loading...": "正在載入...",
        "Testing...": "正在測試...",
        "No Models": "沒有模型",
        "No models found in Ollama. Please pull a model first using 'ollama pull <model>'": "在Ollama中未找到模型。請先使用 'ollama pull <model>' 下載模型。",
        "Failed to connect to Ollama: {}": "連接到Ollama/LM Studio失敗: {}",
        "Failed to fetch models: {}": "獲取模型失敗: {}",
        "Server:": "伺服器:",
        "Host:": "主機:",
        "Port:": "連接埠:",
        "(File not found)": "(檔案未找到)",
        "Presets:": "預設:",
        "No Editor": "無編輯器",
        "Please open a file in the editor first.": "請先在編輯器中開啟檔案。",
        "Code inserted into editor!": "程式碼已插入編輯器！",
        "Connected to {} API. Ready to chat!": "已連接到 {} API。準備聊天！",
        "LLM model loaded successfully!": "LLM模型載入成功！",
        "tkinterweb is not installed": "未安裝tkinterweb",
        "To enable Markdown rendering and interactive features,\nplease install tkinterweb:\n\npip install tkinterweb": "要啟用Markdown渲染和互動功能，\n請安裝tkinterweb：\n\npip install tkinterweb",
        
        # 錯誤訊息
        "File not found during {}: {}": "{}時未找到檔案: {}",
        "Permission denied during {}: {}": "{}時存取被拒絕: {}",
        "Connection failed during {}: {}": "{}時連接失敗: {}",
        "Operation timed out during {}: {}": "{}時操作逾時: {}",
        "Invalid value during {}: {}": "{}時值無效: {}",
        "Missing dependency during {}: {}": "{}時缺少依賴項: {}",
        "Error during {}: {}": "{}時發生錯誤: {}",
        "Connection failed. Please check your internet connection or server settings.": "連接失敗。請檢查您的網際網路連接或伺服器設定。",
        "Request timed out. Please try again.": "請求逾時。請重試。",
        "API key error. Please check your API key in settings.": "API金鑰錯誤。請在設定中檢查您的API金鑰。",
        "Model error. Please check if the model is properly loaded.": "模型錯誤。請檢查模型是否正確載入。",
        "LLM module not installed. Please install llama-cpp-python.": "未安裝LLM模組。請安裝llama-cpp-python。",
        "Failed to initialize LLM": "LLM初始化失敗",
        
        # スキルレベル
        "beginner": "初學者",
        "intermediate": "中級",
        "advanced": "高級",
        
        # 自訂提示詞對話框
        "Edit Custom System Prompt": "編輯自訂系統提示",
        "Enter your custom system prompt. This will be used to instruct the AI on how to respond.": "輸入您的自訂系統提示。這將用於指導AI如何回應。",
        "Tips": "提示",
        "• Use {skill_level} to reference the user's skill level": "• 使用 {skill_level} 引用使用者的技能水準",
        "• Use {language} to reference the output language": "• 使用 {language} 引用輸出語言",
        "• Be specific about the coding style and explanation depth": "• 明確指定程式碼風格和解釋深度",
        "• Include examples of how you want the AI to respond": "• 包含您希望AI如何回應的範例",
        "Presets:": "預設:",
        "Educational": "教育用途",
        "Professional": "專業",
        "Minimal": "最小化",
        "Variables: {skill_level} = 'beginner/intermediate/advanced (with detailed description)', {language} = 'ja/en/zh-CN/zh-TW/auto'": "變數: {skill_level} = '初學者/中級/高級（含詳細描述）', {language} = 'ja/en/zh-CN/zh-TW/auto'",
        "Controls randomness: 0.0 = deterministic, 2.0 = very creative": "控制隨機性: 0.0 = 確定性, 2.0 = 非常有創意",
        "Maximum number of tokens the model can process at once": "模型一次可以處理的最大令牌數（記憶大小）。越大記憶體消耗越多，生成速度越慢",
        "Maximum number of tokens the model will generate in one response": "模型在一次回應中生成的最大令牌數",
        "Penalty for repeating tokens: 1.0 = no penalty, 2.0 = strong penalty": "重複令牌的懲罰: 1.0 = 無懲罰, 2.0 = 強懲罰",
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