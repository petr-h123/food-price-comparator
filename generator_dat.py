import csv
import random

# Nastavení kolik řádků dat se má vygenerovat
POCET_ZAZNAMU = 300

# Seznam obchodů
obchody = ["Lidl", "Albert", "Tesco", "Kaufland", "Billa", "Penny", "Globus"]

# Databáze produktů a jejich orientačních běžných cen (min, max)
produkty_katalog = {
    "Mléčné výrobky": [
        ("Mléko polotučné trvanlivé 1l", 18, 25),
        ("Mléko čerstvé plnotučné 1l", 24, 32),
        ("Máslo 250g", 55, 75),
        ("Jogurt bílý 150g", 10, 16),
        ("Sýr Eidam 30% plátky 100g", 25, 35),
        ("Tvaroh měkký 250g", 20, 30),
        ("Smetana na vaření 12% 200ml", 15, 22),
    ],
    "Pečivo": [
        ("Chléb Šumava 1200g", 35, 49),
        ("Rohlík bílý", 2.5, 4.0),
        ("Bageta střední světlá", 12, 18),
        ("Vánočka s rozinkami 400g", 45, 69),
        ("Kobliha s náplní", 12, 18),
    ],
    "Maso a uzeniny": [
        ("Kuřecí prsní řízky 1kg", 160, 220),
        ("Vepřová krkovice 1kg", 180, 240),
        ("Mleté maso mix 500g", 80, 110),
        ("Šunka dušená výběrová 100g", 25, 35),
        ("Párky vídeňské 1kg", 150, 200),
        ("Klobása grilovací 300g", 60, 90),
    ],
    "Ovoce a zelenina": [
        ("Jablka Gala 1kg", 25, 45),
        ("Banány 1kg", 29, 39),
        ("Brambory 2kg", 35, 59),
        ("Rajčata keříková 500g", 39, 69),
        ("Okurka hadovka 1ks", 15, 29),
        ("Pomeranče 1kg", 30, 50),
    ],
    "Trvanlivé": [
        ("Mouka hladká 1kg", 18, 25),
        ("Cukr krupice 1kg", 25, 32),
        ("Těstoviny špagety 500g", 25, 45),
        ("Rýže parboiled 1kg", 45, 70),
        ("Olej slunečnicový 1l", 40, 65),
        ("Káva instantní 200g", 120, 200),
        ("Čaj ovocný porcovaný", 25, 45),
    ],
    "Nápoje a Alkohol": [
        ("Coca-Cola 2.25l", 35, 49),
        ("Minerální voda 1.5l", 12, 18),
        ("Džus pomeranč 100% 1l", 35, 55),
        ("Pivo světlé výčepní 0.5l plech", 14, 20),
        ("Pivo ležák 0.5l sklo", 18, 28),
        ("Víno bílé suché 0.75l", 90, 150),
    ],
    "Drogerie": [
        ("Toaletní papír 8 rolí", 60, 110),
        ("Prací gel 20 dávek", 150, 250),
        ("Jar na nádobí 900ml", 50, 85),
        ("Sprchový gel 250ml", 40, 70),
        ("Zubní pasta 75ml", 35, 60),
    ],
    "Sladkosti": [
        ("Čokoláda mléčná 100g", 25, 45),
        ("Sušenky polomáčené", 15, 25),
        ("Bonbony gumové 100g", 20, 30),
    ]
}

def generuj_data():
    data = []
    
    # Projde všechny kategorie a produkty
    for kategorie, produkty in produkty_katalog.items():
        for nazev, min_cena, max_cena in produkty:
            # Každý produkt vygeneruje v několika náhodných obchodech (3 až 6 obchodů)
            vybrane_obchody = random.sample(obchody, k=random.randint(3, 6))
            
            for obchod in vybrane_obchody:
                # Generování cen
                cena_bezna = round(random.uniform(min_cena, max_cena), 2)
                
                # Náhodně určí, jak velká je sleva (10% až 50%)
                sleva_procenta = random.randint(10, 50)
                cena_akce = round(cena_bezna * (1 - sleva_procenta / 100), 2)
                
                radek = {
                    "nazev": nazev,
                    "obchod": obchod,
                    "cena_akce": f"{cena_akce:.2f}",
                    "cena_bezna": f"{cena_bezna:.2f}",
                    "kategorie": kategorie
                }
                data.append(radek)
    
    # Promíchá data, aby nebyly seřazené podle kategorií
    random.shuffle(data)
    
    # Zápis do CSV
    filename = "data_potraviny.csv"
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["nazev", "obchod", "cena_akce", "cena_bezna", "kategorie"], delimiter=";")
        writer.writeheader()
        for zaznam in data:
            writer.writerow(zaznam)
            
    print(f"Soubor '{filename}' byl úspěšně vygenerován.")
    print(f"Obsahuje {len(data)} položek (kombinace produktů a obchodů).")

if __name__ == "__main__":
    generuj_data()