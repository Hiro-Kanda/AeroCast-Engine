from .models import WeatherContext


def simple_format(context: WeatherContext) -> str:
    w = context.weather
    lines = [
        f"{w.city}の天気: {w.weather}",
        f"気温：{w.temp}℃ (体感 {w.feels_like}℃)",
        f"湿度：{w.humidity}%",
        f"風速：{w.wind_speed}m/s",
        f"降水確率：{w.rain_probability}%",
    ]

    # 傘の必要性
    if context.umbrella.needed:
        lines.append("⚠️ 傘が必要です。")
    else:
        lines.append("傘は不要です。")

    # 風速の注意喚起
    if context.wind.alert:
        lines.append(f"⚠️ 風が強いです（{w.wind_speed}m/s）。注意してください。")

    # 快適度
    comfort_map = {
        "HOT": "暑い",
        "WARM": "暖かい",
        "COOL": "涼しい",
        "COLD": "寒い",
    }
    comfort_text = comfort_map.get(context.comfort.level, context.comfort.level)
    lines.append(f"体感：{comfort_text}")

    # 雪確率（あれば）
    if w.snow_probability is not None:
        lines.append(f"雪確率：{w.snow_probability}%")
        if w.snow_volume_mm_3h is not None and w.snow_volume_mm_3h > 0:
            lines.append(f"積雪量（3時間）：{w.snow_volume_mm_3h}mm")

    # 観測時刻（あれば）
    if w.observed_at_jst:
        lines.append(f"観測時刻：{w.observed_at_jst}")

    return "\n".join(lines)