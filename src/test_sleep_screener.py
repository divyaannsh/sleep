from sleep_apnea_screener import calculate_stop_bang

def run_tests():
    print("================ RUNNING STOP-BANG SCORING TESTS ================")
    
    # Case 1: Low Risk Patient (0 points)
    case_low = calculate_stop_bang(
        snoring=False,
        tiredness=False,
        observed_apnea=False,
        high_bp=False,
        weight_kg=70,
        height_cm=180,
        age=30,
        neck_circumference_cm=36,
        gender_male=False
    )
    print(f"Case 1 (Low Risk expected): Score={case_low['score']}, Band={case_low['risk_band']}")
    assert case_low['score'] == 0
    assert case_low['risk_band'] == 'low'
    
    # Case 1b: Low Risk Patient with physiological indicators (elevated to Intermediate)
    case_low_physio = calculate_stop_bang(
        snoring=False,
        tiredness=False,
        observed_apnea=False,
        high_bp=False,
        weight_kg=70,
        height_cm=180,
        age=30,
        neck_circumference_cm=36,
        gender_male=False,
        rppg_hrv_rmssd=20.0,
        rppg_bpm=85.0
    )
    print(f"Case 1b (Elevated to Intermediate expected): Score={case_low_physio['score']}, Band={case_low_physio['risk_band']}")
    assert case_low_physio['score'] == 0
    assert case_low_physio['risk_band'] == 'intermediate'
    assert len(case_low_physio['details']['physio_notes']) == 2

    # Case 2: Intermediate Risk Patient (3 points: snoring, tiredness, high_bp)
    case_inter = calculate_stop_bang(
        snoring=True,
        tiredness=True,
        observed_apnea=False,
        high_bp=True,
        weight_kg=80,
        height_cm=175,
        age=45,
        neck_circumference_cm=38,
        gender_male=False
    )
    print(f"Case 2 (Intermediate Risk expected): Score={case_inter['score']}, Band={case_inter['risk_band']}")
    assert case_inter['score'] == 3
    assert case_inter['risk_band'] == 'intermediate'

    # Case 3: High Risk Patient (8 points: all factors active)
    # BMI calculation: weight=115kg, height=170cm -> BMI = 115 / (1.7^2) = 39.79 (>35)
    # Age=55 (>50)
    # Neck=45 (>40)
    case_high = calculate_stop_bang(
        snoring=True,
        tiredness=True,
        observed_apnea=True,
        high_bp=True,
        weight_kg=115,
        height_cm=170,
        age=55,
        neck_circumference_cm=45,
        gender_male=True
    )
    print(f"Case 3 (High Risk expected): Score={case_high['score']}, Band={case_high['risk_band']}")
    assert case_high['score'] == 8
    assert case_high['risk_band'] == 'high'
    
    print("✅ All STOP-BANG scoring tests passed successfully!")

if __name__ == "__main__":
    run_tests()
