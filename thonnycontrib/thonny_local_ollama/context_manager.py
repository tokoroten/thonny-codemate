"""
コンテキストマネージャー
プロジェクト内の複数ファイルのコンテキストを管理し、LLMに提供
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
import ast

from thonny import get_workbench

logger = logging.getLogger(__name__)


@dataclass
class FileContext:
    """ファイルのコンテキスト情報"""
    path: str
    content: str
    imports: List[str]
    functions: List[str]
    classes: List[str]
    is_current: bool = False


class ContextManager:
    """
    プロジェクトのコンテキストを管理するクラス
    関連ファイルを特定し、LLMに適切なコンテキストを提供
    """
    
    def __init__(self, max_files: int = 5, max_file_size: int = 10000):
        self.max_files = max_files
        self.max_file_size = max_file_size
        self._file_cache: Dict[str, FileContext] = {}
    
    def get_project_context(self, current_file: Optional[str] = None) -> List[FileContext]:
        """
        現在のプロジェクトのコンテキストを取得（現在のファイルのみ）
        
        Args:
            current_file: 現在編集中のファイルパス
            
        Returns:
            現在のファイルのコンテキストリスト
        """
        contexts = []
        
        # 現在のファイルを取得
        if not current_file:
            editor = get_workbench().get_editor_notebook().get_current_editor()
            if editor:
                current_file = editor.get_filename()
        
        if not current_file:
            return contexts
        
        current_path = Path(current_file)
        
        # 現在のファイルのコンテキストのみを追加
        current_context = self._analyze_file(current_path)
        if current_context:
            current_context.is_current = True
            contexts.append(current_context)
        
        return contexts
    
    def _find_project_root(self, current_path: Path) -> Path:
        """プロジェクトのルートディレクトリを検索"""
        # 一般的なプロジェクトマーカーを探す
        markers = ['.git', 'pyproject.toml', 'setup.py', 'requirements.txt', '.venv', 'venv']
        
        path = current_path.parent
        while path != path.parent:
            for marker in markers:
                if (path / marker).exists():
                    return path
            path = path.parent
        
        # マーカーが見つからない場合は現在のファイルの親ディレクトリ
        return current_path.parent
    
    def _find_related_files(self, current_file: Path, project_root: Path) -> List[Path]:
        """関連ファイルを検索"""
        related_files = []
        current_imports = set()
        
        # 現在のファイルのインポートを解析
        try:
            if current_file.suffix == '.py':
                with open(current_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                    current_imports = self._extract_imports(tree)
        except Exception as e:
            logger.warning(f"Failed to parse imports from {current_file}: {e}")
        
        # プロジェクト内のPythonファイルを検索（深さ制限付き）
        max_depth = 3  # 最大3階層まで
        processed_count = 0
        max_files_to_check = 100  # 最大100ファイルまでチェック
        
        def find_python_files(path: Path, depth: int = 0):
            nonlocal processed_count
            if depth > max_depth or processed_count > max_files_to_check:
                return
            
            try:
                for item in path.iterdir():
                    if processed_count > max_files_to_check:
                        break
                        
                    # 除外するディレクトリ
                    if item.is_dir():
                        if item.name in ['__pycache__', '.venv', 'venv', '.git', 'node_modules', '.pytest_cache']:
                            continue
                        find_python_files(item, depth + 1)
                    
                    # Pythonファイルの処理
                    elif item.suffix == '.py' and item != current_file:
                        processed_count += 1
                        
                        # ファイルサイズチェック
                        if item.stat().st_size > self.max_file_size:
                            continue
                        
                        yield item
            except PermissionError:
                pass
        
        for py_file in find_python_files(project_root):
            
            # インポート関係をチェック
            try:
                module_name = self._path_to_module(py_file, project_root)
                if module_name in current_imports:
                    related_files.append(py_file)
                    continue
                
                # 逆方向のインポートもチェック
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                    file_imports = self._extract_imports(tree)
                    
                    current_module = self._path_to_module(current_file, project_root)
                    if current_module in file_imports:
                        related_files.append(py_file)
            except Exception as e:
                logger.debug(f"Failed to analyze {py_file}: {e}")
        
        # 同じディレクトリのファイルを優先
        same_dir_files = [f for f in current_file.parent.glob("*.py") 
                         if f != current_file and f.stat().st_size <= self.max_file_size]
        
        # 関連度順にソート（同じディレクトリ → インポート関係）
        sorted_files = []
        for f in same_dir_files:
            if f not in related_files:
                sorted_files.append(f)
        sorted_files.extend(related_files)
        
        return sorted_files
    
    def _analyze_file(self, file_path: Path) -> Optional[FileContext]:
        """ファイルを解析してコンテキストを作成"""
        # キャッシュチェック
        cache_key = str(file_path)
        if cache_key in self._file_cache:
            cached = self._file_cache[cache_key]
            # ファイルが変更されていない場合はキャッシュを使用
            if file_path.stat().st_mtime <= os.path.getmtime(cache_key):
                return cached
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # ASTを解析
            tree = ast.parse(content)
            
            imports = list(self._extract_imports(tree))
            functions = []
            classes = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # トップレベル関数のみ
                    if isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                        functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
            
            context = FileContext(
                path=str(file_path),
                content=content,
                imports=imports,
                functions=functions,
                classes=classes
            )
            
            # キャッシュに保存
            self._file_cache[cache_key] = context
            
            return context
            
        except Exception as e:
            logger.warning(f"Failed to analyze file {file_path}: {e}")
            return None
    
    def _extract_imports(self, tree: ast.AST) -> Set[str]:
        """ASTからインポートを抽出"""
        imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
        
        return imports
    
    def _path_to_module(self, file_path: Path, project_root: Path) -> str:
        """ファイルパスをモジュール名に変換"""
        try:
            relative = file_path.relative_to(project_root)
            parts = relative.with_suffix('').parts
            return '.'.join(parts)
        except ValueError:
            return file_path.stem
    
    def format_context_for_llm(self, contexts: List[FileContext]) -> str:
        """LLM用にコンテキストをフォーマット"""
        if not contexts:
            return ""
        
        formatted = []
        
        # 現在のファイル
        current = next((c for c in contexts if c.is_current), None)
        if current:
            formatted.append(f"=== Current File: {current.path} ===")
            formatted.append(self._format_file_summary(current))
            formatted.append("")
        
        # 関連ファイル
        related = [c for c in contexts if not c.is_current]
        if related:
            formatted.append("=== Related Files ===")
            for context in related:
                formatted.append(f"\n--- {context.path} ---")
                formatted.append(self._format_file_summary(context))
        
        return '\n'.join(formatted)
    
    def _format_file_summary(self, context: FileContext) -> str:
        """ファイルのサマリーをフォーマット"""
        lines = []
        
        if context.imports:
            lines.append(f"Imports: {', '.join(context.imports[:10])}")
        
        if context.classes:
            lines.append(f"Classes: {', '.join(context.classes)}")
        
        if context.functions:
            lines.append(f"Functions: {', '.join(context.functions[:10])}")
        
        # コードの最初の部分を含める（コメントやdocstringを含む可能性）
        code_lines = context.content.split('\n')
        preview_lines = []
        for i, line in enumerate(code_lines[:20]):
            if line.strip() and not line.strip().startswith('#'):
                preview_lines.append(line)
            if len(preview_lines) >= 5:
                break
        
        if preview_lines:
            lines.append("\nCode preview:")
            lines.extend(preview_lines)
        
        return '\n'.join(lines)
    
    def get_context_summary(self) -> Dict[str, any]:
        """現在のコンテキストのサマリーを取得"""
        contexts = self.get_project_context()
        
        return {
            "total_files": len(contexts),
            "current_file": next((c.path for c in contexts if c.is_current), None),
            "related_files": [c.path for c in contexts if not c.is_current],
            "total_classes": sum(len(c.classes) for c in contexts),
            "total_functions": sum(len(c.functions) for c in contexts),
        }