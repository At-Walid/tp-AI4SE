def remise(prix, fidelite):
    if fidelite >= 10:
        return prix * 0.80
    if fidelite >= 5:
        return prix * 0.90
    return prix
