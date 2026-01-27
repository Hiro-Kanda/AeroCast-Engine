def estimate_snow_probability(pop: int, temp_c: float) -> int:
    """
    降水確率（pop）と気温から雪確率を推定する簡易モデル
    
    気温が低いほど雪の確率が高くなるモデル:
    - temp_c <= 0.0: 雪確率 = pop (100%)
    - 0.0 < temp_c < 2.0: 雪確率 = pop * 0.7 (70%)
    - 2.0 <= temp_c < 4.0: 雪確率 = pop * 0.3 (30%)
    - temp_c >= 4.0: 雪確率 = 0 (0%)
    
    Args:
        pop: 降水確率 (%)
        temp_c: 気温 (℃)
        
    Returns:
        推定された雪確率 (%)
    """
    if pop <= 0:
        return 0
    if temp_c <= 0.0:
        return int(pop)
    if temp_c < 2.0:
        return int(pop * 0.7)
    if temp_c < 4.0:
        return int(pop * 0.3)
    return 0