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
        from ..prompts import DEFAULT_SYSTEM_PROMPT_TEMPLATE
        
        self.text_editor.delete("1.0", tk.END)
        self.text_editor.insert("1.0", DEFAULT_SYSTEM_PROMPT_TEMPLATE)
    
    def _insert_educational_preset(self):
        """教育向けプリセットを挿入"""
        from ..prompts import EDUCATIONAL_PRESET_TEMPLATE
        
        self.text_editor.delete("1.0", tk.END)
        self.text_editor.insert("1.0", EDUCATIONAL_PRESET_TEMPLATE)
    
    def _insert_professional_preset(self):
        """プロフェッショナル向けプリセットを挿入"""
        from ..prompts import PROFESSIONAL_PRESET_TEMPLATE
        
        self.text_editor.delete("1.0", tk.END)
        self.text_editor.insert("1.0", PROFESSIONAL_PRESET_TEMPLATE)
    
    def _insert_minimal_preset(self):
        """最小限のプリセットを挿入"""
        from ..prompts import MINIMAL_PRESET_TEMPLATE
        
        self.text_editor.delete("1.0", tk.END)
        self.text_editor.insert("1.0", MINIMAL_PRESET_TEMPLATE)
    
    def _insert_default_preset(self):
        """デフォルトプリセットを挿入"""
        self._insert_default_template()
    
    def _save_and_close(self):
        """保存して閉じる"""
        self.result = self.text_editor.get("1.0", tk.END).strip()
        self.destroy()