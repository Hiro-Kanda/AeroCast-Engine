
class UserFacingError(Exception):
    """ユーザーにそのまま返してよい例外"""
    pass


class CityNotFoundError(UserFacingError):
    pass


class WeatherAPIError(UserFacingError):
    pass


class AmbiguousCityError(UserFacingError):
    """都市名が曖昧で、候補提示が必要な場合"""

    def __init__(self, query: str, candidates: list[str]):
        self.query = query
        self.candidates = candidates
        candidates_str = "、".join(candidates[:5])
        super().__init__(f"地名「{query}」が曖昧です。どちらですか？\n候補: {candidates_str}")