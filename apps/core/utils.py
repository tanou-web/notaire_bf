def montant_en_lettres(n):
    """
    Convertit un nombre en toutes lettres (version simplifiée pour FCFA).
    """
    units = ["", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf"]
    teens = ["dix", "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix-sept", "dix-huit", "dix-neuf"]
    tens = ["", "", "vingt", "trente", "quarante", "cinquante", "soixante", "soixante-dix", "quatre-vingt", "quatre-vingt-dix"]
    
    def _convert_below_1000(n):
        if n == 0: return ""
        res = ""
        c = n // 100
        d = (n % 100)
        
        if c > 0:
            if c == 1: res += "cent "
            else: res += units[c] + " cent "
            
        if d > 0:
            if d < 10: res += units[d]
            elif d < 20: res += teens[d-10]
            else:
                t = d // 10
                u = d % 10
                if t == 7 or t == 9:
                    res += tens[t-1] + "-" + teens[u]
                else:
                    if u == 1: res += tens[t] + " et un"
                    elif u > 1: res += tens[t] + "-" + units[u]
                    else: res += tens[t]
        return res.strip()

    if n == 0: return "zéro franc CFA"
    
    parts = []
    
    # Millions
    m = n // 1000000
    if m > 0:
        if m == 1: parts.append("un million")
        else: parts.append(_convert_below_1000(m) + " millions")
    
    # Milliers
    rem = n % 1000000
    k = rem // 1000
    if k > 0:
        if k == 1: parts.append("mille")
        else: parts.append(_convert_below_1000(k) + " mille")
        
    # Le reste
    rem = rem % 1000
    if rem > 0:
        parts.append(_convert_below_1000(rem))
        
    return " ".join(parts).strip().capitalize() + " francs CFA"
