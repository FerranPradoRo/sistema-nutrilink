"""Fórmulas: IMC, TMB (Mifflin), %grasa (Deurenberg), peso ideal (Devine)."""

def bmi(weight_kg: float, height_m: float) -> float:
    if height_m <= 0: return 0.0
    return round(weight_kg / (height_m ** 2), 2)

def bmr_mifflin(sex: str, weight_kg: float, height_cm: float, age: int) -> float:
    if str(sex).lower().startswith("m"):
        v = 10*weight_kg + 6.25*height_cm - 5*age + 5
    else:
        v = 10*weight_kg + 6.25*height_cm - 5*age - 161
    return round(v, 2)

def bodyfat_deurenberg(bmi_val: float, age: int, sex: str) -> float:
    sex_flag = 1 if str(sex).lower().startswith("m") else 0
    v = 1.2*bmi_val + 0.23*age - 10.8*sex_flag - 5.4
    return round(v, 2)

def ideal_weight_devine(sex: str, height_cm: float) -> float:
    base = 50.0 if str(sex).lower().startswith("m") else 45.5
    extra_cm = max(0.0, height_cm - 152.4)
    add_per_cm = 2.3 / 2.54
    return round(base + add_per_cm * (extra_cm / 1.0), 2)