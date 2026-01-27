import logging
import sys

# ロガー設定：ユーザーにはエラーメッセージを表示しない
logger = logging.getLogger(__name__)
logger.setLevel(logging.CRITICAL)  # CRITICALレベルに設定して、WARNING/ERRORを抑制

# 既存のハンドラーをすべて削除
logger.handlers.clear()

# NullHandlerを使用して、デフォルトの標準エラー出力への出力を防ぐ
handler = logging.NullHandler()
logger.addHandler(handler)
logger.propagate = False  # ルートロガーへの伝播を防ぐ
