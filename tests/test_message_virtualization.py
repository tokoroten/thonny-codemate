"""
メッセージ仮想化のテスト
"""
import pytest
from thonnycontrib.thonny_codemate.message_virtualization import (
    MessageVirtualizer,
    MessageCache
)


class TestMessageVirtualizer:
    """MessageVirtualizerクラスのテスト"""
    
    def test_initialization(self):
        """初期化テスト"""
        virtualizer = MessageVirtualizer(viewport_height=600, message_height=80)
        assert virtualizer.viewport_height == 600
        assert virtualizer.message_height == 80
        assert virtualizer.scroll_position == 0
        assert virtualizer.visible_range == 5
    
    def test_get_visible_messages_empty(self):
        """空のメッセージリストのテスト"""
        virtualizer = MessageVirtualizer()
        messages = []
        
        visible, start, end = virtualizer.get_visible_messages(messages)
        
        assert visible == []
        assert start == 0
        assert end == 0
    
    def test_get_visible_messages_few_messages(self):
        """少数メッセージのテスト"""
        virtualizer = MessageVirtualizer(viewport_height=400, message_height=80)
        messages = [("user", "msg1"), ("assistant", "msg2"), ("user", "msg3")]
        
        visible, start, end = virtualizer.get_visible_messages(messages)
        
        # 少数の場合は全て表示される
        assert len(visible) == 3
        assert start == 0
        assert end == 3
        assert visible[0] == (0, "user", "msg1")
        assert visible[1] == (1, "assistant", "msg2")
        assert visible[2] == (2, "user", "msg3")
    
    def test_get_visible_messages_many_messages(self):
        """大量メッセージの仮想化テスト"""
        virtualizer = MessageVirtualizer(viewport_height=400, message_height=80)
        # 100メッセージを作成
        messages = [(f"sender{i}", f"message{i}") for i in range(100)]
        
        visible, start, end = virtualizer.get_visible_messages(messages)
        
        # ビューポートに表示できるのは5メッセージ(400/80)
        # + 前後の余分(5) = 最大15メッセージ
        assert len(visible) <= 15
        assert start >= 0
        assert end <= 100
    
    def test_force_bottom_scroll(self):
        """最下部強制スクロールのテスト"""
        virtualizer = MessageVirtualizer(viewport_height=400, message_height=80)
        messages = [(f"sender{i}", f"message{i}") for i in range(50)]
        
        visible, start, end = virtualizer.get_visible_messages(messages, force_bottom=True)
        
        # 最後のメッセージが含まれている
        assert end == 50
        last_visible_index = visible[-1][0]
        assert last_visible_index == 49  # 最後のメッセージのindex
    
    def test_update_scroll_position(self):
        """スクロール位置更新のテスト"""
        virtualizer = MessageVirtualizer()
        
        virtualizer.update_scroll_position(100)
        assert virtualizer.scroll_position == 100
        
        # 負の値は0にクランプ
        virtualizer.update_scroll_position(-50)
        assert virtualizer.scroll_position == 0
    
    def test_get_total_height(self):
        """総高さ計算のテスト"""
        virtualizer = MessageVirtualizer(message_height=80)
        
        height = virtualizer.get_total_height(10)
        assert height == 800  # 10 * 80
        
        height = virtualizer.get_total_height(0)
        assert height == 0
    
    def test_should_virtualize(self):
        """仮想化判定のテスト"""
        virtualizer = MessageVirtualizer()
        
        assert not virtualizer.should_virtualize(50)  # 50件は仮想化しない
        assert virtualizer.should_virtualize(150)  # 150件は仮想化する
    
    def test_get_placeholder_html(self):
        """プレースホルダーHTML生成のテスト"""
        virtualizer = MessageVirtualizer(message_height=80)
        
        html = virtualizer.get_placeholder_html(10, 20, 100)
        
        # 前のプレースホルダー: 10 * 80 = 800px
        assert 'height: 800px' in html
        # 後のプレースホルダー: (100 - 20) * 80 = 6400px
        assert 'height: 6400px' in html
    
    def test_scroll_position_calculation(self):
        """スクロール位置に基づく表示範囲計算のテスト"""
        virtualizer = MessageVirtualizer(viewport_height=400, message_height=80)
        messages = [(f"sender{i}", f"message{i}") for i in range(100)]
        
        # スクロール位置を設定（メッセージ10番目あたり）
        virtualizer.update_scroll_position(800)  # 10 * 80
        
        visible, start, end = virtualizer.get_visible_messages(messages)
        
        # 10番目周辺が表示されるはず
        visible_indices = [item[0] for item in visible]
        assert 10 in visible_indices or 9 in visible_indices or 11 in visible_indices


class TestMessageCache:
    """MessageCacheクラスのテスト"""
    
    def test_cache_operations(self):
        """基本的なキャッシュ操作のテスト"""
        cache = MessageCache(max_size=3)
        
        # キャッシュに保存
        cache.set("key1", "<p>html1</p>")
        cache.set("key2", "<p>html2</p>")
        
        # キャッシュから取得
        assert cache.get("key1") == "<p>html1</p>"
        assert cache.get("key2") == "<p>html2</p>"
        assert cache.get("nonexistent") is None
    
    def test_cache_size_limit(self):
        """キャッシュサイズ制限のテスト"""
        cache = MessageCache(max_size=2)
        
        # 3つのアイテムを追加（制限は2）
        cache.set("key1", "html1")
        cache.set("key2", "html2")
        cache.set("key3", "html3")
        
        # 最も古いkey1は削除されている
        assert cache.get("key1") is None
        assert cache.get("key2") == "html2"
        assert cache.get("key3") == "html3"
    
    def test_cache_access_order(self):
        """アクセス順序の管理テスト"""
        cache = MessageCache(max_size=2)
        
        cache.set("key1", "html1")
        cache.set("key2", "html2")
        
        # key1にアクセス（最近使用したことになる）
        cache.get("key1")
        
        # 新しいアイテムを追加
        cache.set("key3", "html3")
        
        # key2が削除され、key1は残る
        assert cache.get("key1") == "html1"
        assert cache.get("key2") is None
        assert cache.get("key3") == "html3"
    
    def test_cache_update(self):
        """既存キーの更新テスト"""
        cache = MessageCache(max_size=3)
        
        cache.set("key1", "html1")
        cache.set("key1", "updated_html1")  # 同じキーで更新
        
        assert cache.get("key1") == "updated_html1"
        assert len(cache.access_order) == 1  # 重複しない
    
    def test_cache_clear(self):
        """キャッシュクリアのテスト"""
        cache = MessageCache()
        
        cache.set("key1", "html1")
        cache.set("key2", "html2")
        
        cache.clear()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert len(cache.access_order) == 0
    
    def test_cache_invalidate(self):
        """特定キーの無効化テスト"""
        cache = MessageCache()
        
        cache.set("key1", "html1")
        cache.set("key2", "html2")
        
        cache.invalidate("key1")
        
        assert cache.get("key1") is None
        assert cache.get("key2") == "html2"
        assert "key1" not in cache.access_order