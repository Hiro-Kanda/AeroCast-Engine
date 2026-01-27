import logging
import sys

# ロガー設定：ユーザーにはエラーメッセージを表示しない
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

# ハンドラーが既に設定されている場合は追加しない
if not logger.handlers:
    # NullHandlerを使用して、デフォルトの標準エラー出力への出力を防ぐ
    # 必要に応じて、ファイルハンドラーなどを追加可能
    handler = logging.NullHandler()
    logger.addHandler(handler)
    logger.propagate = False  # ルートロガーへの伝播を防ぐ
