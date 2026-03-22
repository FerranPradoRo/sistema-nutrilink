def calc_bmi(weight_kg: float, height_cm: float) -> float:
    if height_cm <= 0:
        return 0.0
    h = height_cm / 100
    return round(weight_kg / (h * h), 2)

def calc_body_fat_pct(sex: str, age: int, bmi: float) -> float:
    # Fórmula estimada tipo Deurenberg
    sex_factor = 1 if sex == "M" else 0
    value = (1.20 * bmi) + (0.23 * age) - (10.8 * sex_factor) - 5.4
    return round(max(0, value), 2)

def calc_ideal_weight(sex: str, height_cm: float) -> float:
    inches = height_cm / 2.54
    base_inches = max(0, inches - 60)
    if sex == "M":
        value = 50 + (2.3 * base_inches)
    else:
        value = 45.5 + (2.3 * base_inches)
    return round(value, 2)

def calc_bmr(sex: str, age: int, weight_kg: float, height_cm: float) -> float:
    if sex == "M":
        value = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        value = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    return round(value, 2)

def build_metrics(sex: str, age: int, weight_kg: float, height_cm: float) -> dict:
    bmi = calc_bmi(weight_kg, height_cm)
    return {
        "bmi": bmi,
        "body_fat_pct": calc_body_fat_pct(sex, age, bmi),
        "ideal_weight": calc_ideal_weight(sex, height_cm),
        "bmr": calc_bmr(sex, age, weight_kg, height_cm),
    }