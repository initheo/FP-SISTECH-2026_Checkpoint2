"""
Fungsi compute_severity di sini disalin dari notebook
01_pseudo_labeling_feature_engineering.ipynb (Tahap 3), agar pengujian bisa
dijalankan mandiri lewat pytest tanpa harus menjalankan seluruh notebook.
Jika parameter di notebook diubah, salinan di sini wajib disesuaikan juga.
"""
import numpy as np
import pandas as pd

SEVERITY_BASE = {
    'HOMICIDE': 95, 'CRIM SEXUAL ASSAULT': 88, 'CRIMINAL SEXUAL ASSAULT': 88, 'KIDNAPPING': 80,
    'ROBBERY': 55, 'ARSON': 60, 'BATTERY': 52,
    'BURGLARY': 35, 'ASSAULT': 38, 'THEFT': 32, 'NARCOTICS': 40,
    'MOTOR VEHICLE THEFT': 34, 'WEAPONS VIOLATION': 42, 'OFFENSE INVOLVING CHILDREN': 45,
    'CRIMINAL DAMAGE': 20, 'DECEPTIVE PRACTICE': 15, 'CRIMINAL TRESPASS': 18,
    'PUBLIC PEACE VIOLATION': 12, 'LIQUOR LAW VIOLATION': 5, 'GAMBLING': 8,
}
DEFAULT_SEVERITY = 25

WEAPON_BONUS = [
    (('HANDGUN', 'FIREARM'), 27),
    (('KNIFE', 'CUTTING'), 18),
    (('ARMED',), 15),
]

ADDITIVE_MODIFIERS = {
    'AGGRAVATED': 15, 'CHILD': 15, 'DOMESTIC': 8,
    'FORCIBLE': 10, 'FROM PERSON': 10, 'OVER $500': 5,
}

SUBTRACTIVE_MODIFIERS = {'ATTEMPT': -10, 'UNDER $500': -5}


def compute_severity(primary_type, description):
    base = SEVERITY_BASE.get(str(primary_type).upper().strip(), DEFAULT_SEVERITY)
    desc = str(description).upper() if pd.notna(description) else ''

    weapon_score = 0
    for keywords, bonus in WEAPON_BONUS:
        if any(keyword in desc for keyword in keywords):
            weapon_score = bonus
            break

    additive = sum(value for keyword, value in ADDITIVE_MODIFIERS.items() if keyword in desc)
    subtractive = sum(value for keyword, value in SUBTRACTIVE_MODIFIERS.items() if keyword in desc)

    score = base + weapon_score + additive + subtractive
    return float(np.clip(score, 0, 100))


def test_robbery_armed_handgun_matches_anchor_example():
    assert compute_severity('ROBBERY', 'ARMED: HANDGUN') == 82


def test_battery_domestic_matches_anchor_example():
    assert compute_severity('BATTERY', 'DOMESTIC BATTERY SIMPLE') == 60


def test_theft_under_500_matches_anchor_example():
    assert compute_severity('THEFT', 'UNDER $500') == 27


def test_homicide_matches_anchor_example():
    assert compute_severity('HOMICIDE', 'SIMPLE') == 95


def test_weapon_bonus_is_not_double_counted():
    score = compute_severity('ROBBERY', 'ARMED: HANDGUN')
    assert score == 82