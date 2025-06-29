"""
メッセージの仮想化によるパフォーマンス最適化
大量のメッセージがある場合でも高速にレンダリング
"""
from typing import List, Tuple, Optional
import math


class MessageVirtualizer:
    """
    メッセージリストの仮想化を管理するクラス
    画面に表示される範囲のメッセージのみをレンダリング
    """
    
    def __init__(self, viewport_height: int = 600, message_height: int = 80):
        """
        Args:
            viewport_height: ビューポートの高さ（ピクセル）
            message_height: 1メッセージの平均高さ（ピクセル）
        """
        self.viewport_height = viewport_height
        self.message_height = message_height
        self.scroll_position = 0
        self.visible_range = 5  # 前後に余分にレンダリングする数
    
    def get_visible_messages(
        self, 
        messages: List[Tuple[str, str]], 
        force_bottom: bool = False
    ) -> Tuple[List[Tuple[int, str, str]], int, int]:
        """
        表示すべきメッセージを計算
        
        Args:
            messages: 全メッセージリスト
            force_bottom: 最下部にスクロールするか
            
        Returns:
            (表示するメッセージのリスト[(index, sender, text)], 開始インデックス, 終了インデックス)
        """
        if not messages:
            return [], 0, 0
        
        total_messages = len(messages)
        messages_per_viewport = math.ceil(self.viewport_height / self.message_height)
        
        if force_bottom:
            # 最下部を表示
            end_index = total_messages
            start_index = max(0, end_index - messages_per_viewport - self.visible_range)
        else:
            # 現在のスクロール位置から計算
            first_visible = int(self.scroll_position / self.message_height)
            start_index = max(0, first_visible - self.visible_range)
            end_index = min(
                total_messages,
                first_visible + messages_per_viewport + self.visible_range
            )
        
        # 表示するメッセージを抽出
        visible_messages = []
        for i in range(start_index, end_index):
            sender, text = messages[i]
            visible_messages.append((i, sender, text))
        
        return visible_messages, start_index, end_index
    
    def update_scroll_position(self, position: int):
        """スクロール位置を更新"""
        self.scroll_position = max(0, position)
    
    def get_total_height(self, message_count: int) -> int:
        """全メッセージの高さを計算"""
        return message_count * self.message_height
    
    def should_virtualize(self, message_count: int) -> bool:
        """仮想化が必要かどうかを判定"""
        # 100件以上のメッセージがある場合は仮想化を推奨
        return message_count > 100
    
    def get_placeholder_html(self, start_index: int, end_index: int, total_count: int) -> str:
        """表示範囲外のメッセージ用のプレースホルダーHTML"""
        before_height = start_index * self.message_height
        after_height = (total_count - end_index) * self.message_height
        
        html = ""
        if before_height > 0:
            html += f'<div style="height: {before_height}px;"></div>'
        
        # ここに実際のメッセージが入る
        
        if after_height > 0:
            html += f'<div style="height: {after_height}px;"></div>'
        
        return html


class MessageCache:
    """レンダリング済みHTMLのキャッシュ"""
    
    def __init__(self, max_size: int = 200):
        self.cache = {}
        self.max_size = max_size
        self.access_order = []
    
    def get(self, key: str) -> Optional[str]:
        """キャッシュからHTMLを取得"""
        if key in self.cache:
            # アクセス順を更新
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None
    
    def set(self, key: str, html: str):
        """キャッシュにHTMLを保存"""
        if key in self.cache:
            self.access_order.remove(key)
        elif len(self.cache) >= self.max_size:
            # 最も古いアイテムを削除
            oldest = self.access_order.pop(0)
            del self.cache[oldest]
        
        self.cache[key] = html
        self.access_order.append(key)
    
    def clear(self):
        """キャッシュをクリア"""
        self.cache.clear()
        self.access_order.clear()
    
    def invalidate(self, key: str):
        """特定のキャッシュを無効化"""
        if key in self.cache:
            del self.cache[key]
            self.access_order.remove(key)