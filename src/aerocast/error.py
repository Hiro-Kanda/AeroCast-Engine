
class UserFacingError(Exception):
    """ユーザーにそのまま返してよい例外"""
    pass


class CityNotFoundError(UserFacingError):
    pass


class WeatherAPIError(UserFacingError):
    pass