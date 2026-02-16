# ai_model.py

def ai_signal(score):

    if score >= 3:
        return "Sinyal Beli Kuat"
    elif score == 2:
        return "Potensi Naik"
    else:
        return "Belum Ada Sinyal"
