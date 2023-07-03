

prefixeswithshortj = ("bij", "fidej", "Foroj", "foroj", "ju_rej", "multij", "praej", "quadrij",
                      "rej", "retroj", "se_mij", "sesquij", "u_nij", "introj")


def toascii(txt):
    for source, replacement in [("æ", "ae"), ("Æ", "Ae"), ("œ", "oe"), ("Œ", "Oe"),
                                ("ä", "a"), ("ë", "e"), ("ï", "i"), ("ö", "o"), ("ü", "u"), ("ÿ", "u")]:
        txt = txt.replace(source, replacement)
    return txt
