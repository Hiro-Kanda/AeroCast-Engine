"""
リトライ機能（バックオフ付き）
429/5xxエラーに対して指数バックオフで再試行
"""
import time
import random
from typing import Callable, TypeVar, Optional
from functools import wraps

from requests import RequestException
from requests.exceptions import HTTPError

from .logger import logger

T = TypeVar('T')


def exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    retryable_status_codes: set[int] = {429, 500, 502, 503, 504}
) -> Callable:
    """
    指数バックオフでリトライするデコレータ
    
    Args:
        max_retries: 最大リトライ回数
        base_delay: ベース遅延時間（秒）
        max_delay: 最大遅延時間（秒）
        jitter: ジッター（ランダムな遅延）を追加するか
        retryable_status_codes: リトライ対象のHTTPステータスコード
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except HTTPError as e:
                    status_code = e.response.status_code if hasattr(e, 'response') and e.response else None
                    
                    # リトライ可能なエラーかチェック
                    if status_code in retryable_status_codes and attempt < max_retries:
                        delay = min(
                            base_delay * (2 ** attempt),
                            max_delay
                        )
                        
                        if jitter:
                            # ジッターを追加（0〜20%のランダムな遅延）
                            delay = delay * (1 + random.uniform(0, 0.2))
                        
                        logger.debug(
                            f"HTTP {status_code}エラーが発生しました。"
                            f"{delay:.2f}秒後にリトライします（試行 {attempt + 1}/{max_retries + 1}）"
                        )
                        time.sleep(delay)
                        last_exception = e
                        continue
                    else:
                        # リトライ不可能なエラーまたは最大リトライ回数に達した
                        raise
                        
                except RequestException as e:
                    # ネットワークエラーなどもリトライ
                    if attempt < max_retries:
                        delay = min(
                            base_delay * (2 ** attempt),
                            max_delay
                        )
                        
                        if jitter:
                            delay = delay * (1 + random.uniform(0, 0.2))
                        
                        logger.debug(
                            f"リクエストエラーが発生しました: {type(e).__name__}。"
                            f"{delay:.2f}秒後にリトライします（試行 {attempt + 1}/{max_retries + 1}）"
                        )
                        time.sleep(delay)
                        last_exception = e
                        continue
                    else:
                        raise
            
            # すべてのリトライが失敗した場合
            if last_exception:
                raise last_exception
            raise RuntimeError("予期しないエラーが発生しました")
        
        return wrapper
    return decorator


def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    retryable_status_codes: set[int] = {429, 500, 502, 503, 504}
) -> T:
    """
    関数を指数バックオフでリトライする（関数形式）
    
    使用例:
        result = retry_with_backoff(lambda: api_call(), max_retries=5)
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except HTTPError as e:
            status_code = e.response.status_code if hasattr(e, 'response') and e.response else None
            
            if status_code in retryable_status_codes and attempt < max_retries:
                delay = min(base_delay * (2 ** attempt), max_delay)
                if jitter:
                    delay = delay * (1 + random.uniform(0, 0.2))
                
                logger.debug(
                    f"HTTP {status_code}エラー。{delay:.2f}秒後にリトライ（{attempt + 1}/{max_retries + 1}）"
                )
                time.sleep(delay)
                last_exception = e
                continue
            else:
                raise
                
        except RequestException as e:
            if attempt < max_retries:
                delay = min(base_delay * (2 ** attempt), max_delay)
                if jitter:
                    delay = delay * (1 + random.uniform(0, 0.2))
                
                logger.debug(
                    f"リクエストエラー: {type(e).__name__}。"
                    f"{delay:.2f}秒後にリトライ（{attempt + 1}/{max_retries + 1}）"
                )
                time.sleep(delay)
                last_exception = e
                continue
            else:
                raise
    
    if last_exception:
        raise last_exception
    raise RuntimeError("予期しないエラーが発生しました")
