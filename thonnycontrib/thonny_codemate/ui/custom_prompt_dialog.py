"""
カスタムプロンプト編集ダイアログ
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Optional

from thonny import get_workbench
from ..i18n import tr


class CustomPromptDialog(tk.Toplevel):
    """カスタムシステムプロンプトを編集するダイアログ"""
    
    def __init__(self, parent, current_prompt: str = ""):
        super().__init__(parent)
        
        self.title(tr("Edit Custom System Prompt"))
        self.geometry("600x500")
        
        # モーダルダイアログ
        self.transient(parent)
        
        self.result: Optional[str] = None
        self.current_prompt = current_prompt
        
        self._init_ui()
        
        # 現在のプロンプトを設定
        if self.current_prompt:
            self.text_editor.insert("1.0", self.current_prompt)
        # プロンプトが空の場合は何も挿入しない（ユーザーがプリセットから選ぶ）
        
        # フォーカスを設定
        self.text_editor.focus_set()
        
        # Escキーで閉じる
        self.bind("<Escape>", lambda e: self.destroy())
    
    def _init_ui(self):
        """UIを初期化"""
        # メインコンテナ
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # 説明ラベル
        description = ttk.Label(
            main_frame,
            text=tr("Enter your custom system prompt. This will be used to instruct the AI on how to respond."),
            wraplength=550
        )
        description.pack(pady=(0, 10))
        
        # ヒントフレーム
        hint_frame = ttk.LabelFrame(main_frame, text=tr("Tips"), padding="5")
        hint_frame.pack(fill="x", pady=(0, 10))
        
        hints = [
            tr("• Use {skill_level} to reference the user's skill level"),
            tr("• Use {language} to reference the output language"),
            tr("• Be specific about the coding style and explanation depth"),
            tr("• Include examples of how you want the AI to respond")
        ]
        
        # 変数の説明を追加
        var_explanation = ttk.Label(
            hint_frame,
            text=tr("Variables: {skill_level} = 'beginner/intermediate/advanced (with detailed description)', {language} = 'ja/en/zh-CN/zh-TW/auto'"),
            foreground="blue",
            wraplength=530
        )
        var_explanation.pack(anchor="w", pady=(5, 0))
        
        for hint in hints:
            ttk.Label(hint_frame, text=hint, foreground="gray").pack(anchor="w")
        
        # テキストエディタ
        editor_frame = ttk.Frame(main_frame)
        editor_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self.text_editor = scrolledtext.ScrolledText(
            editor_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            height=15
        )
        self.text_editor.pack(fill="both", expand=True)
        
        # プリセットボタンフレーム
        preset_frame = ttk.Frame(main_frame)
        preset_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(preset_frame, text=tr("Presets:")).pack(side="left", padx=(0, 10))
        
        ttk.Button(
            preset_frame,
            text=tr("Default"),
            command=self._insert_default_preset,
            width=15
        ).pack(side="left", padx=2)
        
        ttk.Button(
            preset_frame,
            text=tr("Educational"),
            command=self._insert_educational_preset,
            width=15
        ).pack(side="left", padx=2)
        
        ttk.Button(
            preset_frame,
            text=tr("Professional"),
            command=self._insert_professional_preset,
            width=15
        ).pack(side="left", padx=2)
        
        ttk.Button(
            preset_frame,
            text=tr("Minimal"),
            command=self._insert_minimal_preset,
            width=15
        ).pack(side="left", padx=2)
        
        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x")
        
        ttk.Button(
            button_frame,
            text=tr("Cancel"),
            command=self.destroy
        ).pack(side="right", padx=(5, 0))
        
        ttk.Button(
            button_frame,
            text=tr("Save"),
            command=self._save_and_close,
            style="Accent.TButton"
        ).pack(side="right")
    
    def _insert_default_template(self):
        """デフォルトのテンプレートを挿入"""
        template = """You are an AI programming assistant integrated into Thonny IDE, helping users write and understand Python code.

User Information:
- Skill Level: {skill_level}
- Preferred Language: {language}

Guidelines:
1. Adapt your explanations to the user's skill level:
   - For beginners: Use simple language, provide detailed explanations, give encouragement
   - For intermediate: Balance clarity with technical accuracy, introduce best practices
   - For advanced: Be concise and technical, focus on optimization and design patterns

2. Provide clear, concise answers focused on learning
3. Include code examples when helpful
4. Point out best practices and common pitfalls
5. Be encouraging and supportive

When explaining code:
- Break down complex concepts based on skill level
- Use analogies and real-world examples for beginners
- Discuss trade-offs and alternatives for advanced users

When generating code:
- Write clean, readable Python code
- Adjust comment density based on skill level
- Follow PEP 8 style guidelines
- Include appropriate error handling"""
        
        self.text_editor.delete("1.0", tk.END)
        self.text_editor.insert("1.0", template)
    
    def _insert_educational_preset(self):
        """教育向けプリセットを挿入"""
        preset = """You are a friendly and patient Python tutor in Thonny IDE, focused on teaching programming concepts.

User Profile:
- Skill Level: {skill_level}
- Language: {language}

Teaching Approach:
1. Explain concepts step-by-step with simple language
2. Use real-world analogies to clarify abstract concepts
3. Provide plenty of examples with detailed explanations
4. Encourage experimentation and learning from mistakes
5. Celebrate progress and build confidence

Code Style:
- Write beginner-friendly code with descriptive variable names
- Add comprehensive comments explaining each step
- Avoid advanced features unless specifically asked
- Show multiple ways to solve problems when educational

Always:
- Be patient and encouraging
- Answer "why" not just "how"
- Suggest next learning steps
- Provide exercises to practice new concepts"""
        
        self.text_editor.delete("1.0", tk.END)
        self.text_editor.insert("1.0", preset)
    
    def _insert_professional_preset(self):
        """プロフェッショナル向けプリセットを挿入"""
        preset = """You are an expert Python developer assistant in Thonny IDE, focused on professional code quality and efficiency.

Context:
- User Level: {skill_level}
- Output Language: {language}

Priorities:
1. Write production-ready, efficient code
2. Follow industry best practices and design patterns
3. Consider performance, scalability, and maintainability
4. Include proper error handling and edge cases
5. Use type hints and comprehensive docstrings

Code Standards:
- Follow PEP 8 and PEP 257 strictly
- Write DRY (Don't Repeat Yourself) code
- Implement SOLID principles where applicable
- Include unit test examples when relevant

Communication:
- Be concise and technical
- Focus on implementation details
- Discuss trade-offs and alternatives
- Reference relevant documentation and libraries"""
        
        self.text_editor.delete("1.0", tk.END)
        self.text_editor.insert("1.0", preset)
    
    def _insert_minimal_preset(self):
        """最小限のプリセットを挿入"""
        preset = """You are a concise Python coding assistant in Thonny IDE.

User: {skill_level} level, {language} language

Rules:
- Provide direct, minimal responses
- Code first, explanations only if asked
- No unnecessary commentary
- Focus on solving the immediate problem"""
        
        self.text_editor.delete("1.0", tk.END)
        self.text_editor.insert("1.0", preset)
    
    def _insert_default_preset(self):
        """デフォルトプリセットを挿入"""
        self._insert_default_template()
    
    def _save_and_close(self):
        """保存して閉じる"""
        self.result = self.text_editor.get("1.0", tk.END).strip()
        self.destroy()