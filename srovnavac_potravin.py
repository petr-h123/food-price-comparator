import os
import unicodedata
import csv
import questionary
import difflib
import random
import sys
import pyfiglet
import time
from rich import print
from rich.box import DOUBLE
from rich.panel import Panel
from rich.align import Align
from rich.console import Console
from rich.table import Table
from datetime import datetime
from rich.text import Text
console = Console()

# --------------------------------------------|URČENÍ CEST SOUBORŮ|--------------------------------------------------------
ADRESAR_PROJEKTU = os.path.dirname(os.path.abspath(__file__))

CESTA_DATABAZE = os.path.join(ADRESAR_PROJEKTU, 'data_potraviny.csv')
CESTA_SVATKY = os.path.join(ADRESAR_PROJEKTU, 'svatky.csv')
CESTA_SEZNAMU = os.path.join(ADRESAR_PROJEKTU, "nakupni_seznam.txt")


# --------------------------------------------|DEFINICE FUNKCÍ|--------------------------------------------------------
def uvodni_obrazovka():
    console.clear()
    
    f = pyfiglet.Figlet(font='ansi_shadow')
    velky_text = f.renderText('SROVNAVAC   POTRAVIN')
    
    text_nadpis = Text(velky_text, style="gold1")
    
    console.print(
        Panel(
            Align.center(text_nadpis),
            subtitle="[dim][i]Všechna práva vyhrazena © 2026[/][/]",
            subtitle_align="center",
            border_style="orange3",
            padding=(1, 0, 0, 0),
            expand=True
        )
    )
    
def datum_svatek():
    # Aktuální datum a svátek
    dnesni_datum = datetime.now().strftime("%d. %m. %Y")
    nyni = datetime.now()
    dnesni_klic = nyni.strftime("%d.%m.")
    svatek = "neznámý oslavenec"  # Výchozí hodnota, pokud se nic nenajde

    try:
        with open(CESTA_SVATKY, mode='r', encoding='utf-8') as f:
            ctenar = csv.DictReader(f, delimiter=';')
            for radek in ctenar:
                if radek['datum'] == dnesni_klic:
                    svatek = radek['jmeno']
                    break
    except FileNotFoundError:
        svatek = "[red][i]soubor nenalezen[/][/]"

    aktualni_datum = f'[#fff700]Dnes je [#ffc400]{dnesni_datum}[/] a má svátek [#ffc400]{svatek}[/].[/]'
    print(Align.center(Panel(
        aktualni_datum,
        border_style="#fff700",
        )))  
        
def normalizuj(text):
    """
    Ze vstupu(string) odstraní háčky, čárky, převede na malá písmena a smaže mezery.
    Vrací string
    """
    if not text:
        return ""
    text = text.lower().strip()
    text = unicodedata.normalize('NFKD', text)
    text = "".join([c for c in text if not unicodedata.combining(c)])
    return text

def vyhledej_produkt_v_db(hledany_produkt):
    """
    Vyhledá produkt v databázi.
    Vrací seznam slovníků s výskyty hledaného produktu.
    """
    vysledky = []
    hledany_normalizovany = normalizuj(hledany_produkt)
    with open(CESTA_DATABAZE, mode='r', encoding='utf-8') as soubor:
            ctenar = csv.DictReader(soubor, delimiter=';')
            for radek in ctenar:
                nazev_v_db_normalizovany = normalizuj(radek['nazev'])
                if hledany_normalizovany in nazev_v_db_normalizovany:
                    vysledky.append(radek)
    return vysledky

def zjisteni_poctu(seznam):
    if not seznam:
        return 0
    return 1 + zjisteni_poctu(seznam[1:])    

def serad_vysledky(seznam_vysledku, kriterium, smer):
    """
    Řadí seznam produktů.
    """
    # Pokud je smer "Vzestupně", reverse bude False. Pokud "Sestupně", reverse bude True.
    je_reverse = (smer == "Sestupně")
    
    mozne_kriteria = {
        "Podle akční ceny": lambda x: float(x['cena_akce']),
        "Podle běžné ceny": lambda x: float(x['cena_bezna']),
        "Podle největší akce": lambda x: float(x['cena_bezna']) - float(x['cena_akce']),
        "Podle názvu obchodu": lambda x: x['obchod'].lower()
    }

    vybrany_klic = mozne_kriteria.get(kriterium, lambda x: float(x['cena_akce']))

    return sorted(seznam_vysledku, key=vybrany_klic, reverse=je_reverse)

def vyhledat_pr_podl_nazvu():
    """
    Zajišťuje kompletní proces vyhledávání produktu podle názvu v uživatelském rozhraní.
    
    Funkce provede následující kroky:
    1. Získá bezpečný vstup od uživatele pomocí našeptávače.
    2. Vyhledá odpovídající položky v databázi.
    3. Pokud jsou data nalezena, nabídne uživateli interaktivní menu pro výběr 
       kritéria a směru řazení (cena, obchod, sleva).
    4. Výsledky zformátuje do přehledné tabulky a zobrazí je v panelu.
    
    Vstupy: Využívá vstupy v terminálu
    Vrací: None
    """    
    hledany_vyraz = ziskej_bezpecny_vstup_produktu("Zadejte název produktu:")
    if not hledany_vyraz:
        print("[i][yellow]Výběr zrušen. Návrat do menu...[/][/]\n")
        return
    
    data_produktu = vyhledej_produkt_v_db(hledany_vyraz)
    if data_produktu:
        
        # Výběr kritéria
        kriterium = questionary.select(
            "Podle čeho se mají výsledky řadit?",
            choices=[
                "Podle akční ceny",
                "Podle běžné ceny",
                "Podle největší akce",
                "Podle názvu obchodu",
                "Neseřazovat"
            ],
            instruction=' ',
            qmark='❓',
            pointer='👉',
            style=questionary.Style([('highlighted', 'fg:cyan bold')])
        ).ask()
        
        if kriterium and kriterium != "Neseřazovat":
            smer = questionary.select(
            "Jak chcete výsledky seřadit?",
            choices=[
                "Vzestupně",
                "Sestupně",
            ],
            instruction=' ',
            qmark='❓',
            pointer='👉',
            style=questionary.Style([('highlighted', 'fg:cyan bold')])
        ).ask()

            if smer:
                print('\n')
                data_produktu = serad_vysledky(data_produktu, kriterium, smer)   
        
        # Objekty tabulky 
              
        tabulka = Table(
            show_header=True, 
            header_style="#FF00FF bold", 
            expand=False, 
            title=f'[i][b]Výsledky pro:[/][/] [#fffe36][b]{hledany_vyraz}[/][/]',
            title_style=''
            )        
        
        tabulka.add_column("Obchod", style="dim")
        tabulka.add_column("Akční cena", justify="right", style="green bold")
        tabulka.add_column("Běžná cena", justify="right", style="red")
        tabulka.add_column("Název produktu", justify="left", style="dim")
        tabulka.add_column("Kategorie", justify="center")

        # Naplnění tabulky všemi řádky z listu data_produktu
        for polozka in data_produktu:
            tabulka.add_row(
                polozka['obchod'],
                f"{polozka['cena_akce']} Kč",
                f"{polozka['cena_bezna']} Kč",
                polozka['nazev'],
                polozka['kategorie']
            )

        # Vložení tabulky do panelu
        console.print(tabulka)        
        vracak = console.input("[dim]Stiskněte Enter pro návrat do menu...[/]")
        if not vracak:
            console.print("[i][yellow]Návrat do menu...[/][/]\n")
        return
            
        
    else:
        console.print("[red][i]Vámi hledaný produkt nebyl nalezen.[/i][/red]")
        
def souboj_obchodu():
    """
    Porovnává celkovou cenu nákupního košíku napříč dostupnými obchodními řetězci.
    Uživatel zadává produkty postupně pomocí našeptávače.
    """
    seznam_veci = []
    
    console.print(Panel(
'''
Zadávejte produkty jeden po druhém.
Program nalezne optimální volbu obchodů pro nákup těchto produktů.\n
Až budete hotovi, [bold yellow]stiskněte Enter naprázdno[/] pro vyhodnocení.
''',
        style="orange3",
        expand=False
    ))

    # --- 1. FÁZE: SBĚR PRODUKTŮ ---
    while True:
        
        pocet = zjisteni_poctu(seznam_veci)
        tazaci_text = f"Přidat {pocet + 1}. produkt:"
        novy_produkt = ziskej_bezpecny_vstup_produktu(tazaci_text)
    
        if not novy_produkt:
            break
        
        if len(novy_produkt.strip()) < 3 or not vyhledej_produkt_v_db(novy_produkt):
            console.print(f"   [red][b]✘ Špatný vstup:[/][/] {novy_produkt}")
            continue
            
        seznam_veci.append(novy_produkt)
        console.print(f"   [green][b]✔ Přidáno:[/][/] {novy_produkt}")

    if not seznam_veci:
        console.print("\n[i][yellow]Nebyly zadány žádné produkty. Návrat do menu...[/][/]\n")
        return

    # Výpočet
    obchody = ["Lidl", "Albert", "Tesco", "Kaufland", "Billa", "Penny", "Globus"]
    vysledky_srovnani = []

    for obchod in obchody:
        celkova_cena = 0
        pocet_nalezenych = 0

        for vec in seznam_veci:
            data = vyhledej_produkt_v_db(vec.strip())
            
            nasel_v_obchode = False
            for polozka in data:
                if polozka['obchod'] == obchod:
                    celkova_cena += float(polozka['cena_akce'])
                    pocet_nalezenych += 1
                    nasel_v_obchode = True
                    break 
            
        # Uložíme výsledek jen pokud obchod má VŠECHNY položky ze seznamu
        if pocet_nalezenych == len(seznam_veci):
            vysledky_srovnani.append([obchod, celkova_cena])

    # Výpis    
    if vysledky_srovnani:
        vysledky_srovnani.sort(key=lambda x: x[1])
        nejlevnejsi_cena = vysledky_srovnani[0][1]

        # Vytvoření tabulky
        tabulka = Table(title=f"[bold yellow]VÝSLEDKY SOUBOJE pro {len(seznam_veci)} položek[/]", 
                        header_style="#FF00FF bold"
                        )
        tabulka.add_column("Pořadí", justify="center", style="dim")
        tabulka.add_column("Obchod", style="bold")
        tabulka.add_column("Celková cena", justify="right")
        tabulka.add_column("Rozdíl", justify="right", style="red")

        for i, (obchod, cena) in enumerate(vysledky_srovnani):
            rozdil = cena - nejlevnejsi_cena
            
            # Stylování vítěze
            if i == 0:
                styl_radku = "bold green"
                text_rozdil = "[bold green]NEJLEVNĚJŠÍ[/]"
                ikona = "🏆 "
            else:
                styl_radku = "white"
                text_rozdil = f"+ {rozdil:.2f} Kč"
                ikona = ""

            tabulka.add_row(
                str(i + 1) + ".",
                ikona + obchod, 
                f"{cena:.2f} Kč", 
                text_rozdil,
                style=styl_radku
            )

        console.print(tabulka)
        
        # Výpis položek, které se počítaly (pro kontrolu)
        console.print(f"\n[dim]Hledané položky: {', '.join(seznam_veci)}[/dim]", justify="center")

    else:
        console.print(Panel("[red]Bohužel, žádný jeden obchod nemá v akci [bold]všechny[/bold] hledané položky současně.[/]", title="Výsledek", border_style="red"))
    
    vracak = console.input("\n[dim]Stiskněte Enter pro návrat do menu...[/]")
    if not vracak:
        console.print("[i][yellow]Návrat do menu...[/][/]\n")
        return

def ziskej_bezpecny_vstup_produktu(tazaci_text):
    """
    Načte všechny názvy produktů z CSV a nabídne uživateli
    chytrý vstup s našeptáváním.
    Pokud uživatel zadá text mimo seznam, zkusí najít shodu.
    """
    # 1. Načte všechny unikátní názvy produktů pro našeptávač
    vsechny_nazvy = set()
    try:
        with open(CESTA_DATABAZE, mode='r', encoding='utf-8') as soubor:
            ctenar = csv.DictReader(soubor, delimiter=';')
            for radek in ctenar:
                vsechny_nazvy.add(radek['nazev'])
    except FileNotFoundError:
        console.print("[bold red]Soubor databáze nenalezen! Nelze použít našeptávač.[/]")
        return None
    
    lista_nazvu = sorted(list(vsechny_nazvy))

    # 2. Zobrazí vstup s našeptáváním
    vstup_uzivatele = questionary.autocomplete(
        tazaci_text,
        choices=lista_nazvu,
        qmark='\n❓',
        style=questionary.Style([('answer', 'fg:yellow bold')]),
        ignore_case=True,
        match_middle=True,
    ).ask()

    if not vstup_uzivatele:
        return None

    # 3. Validace a Fuzzy logika ("Měli jste na mysli...?")
    # Najde nejpodobnější slovo v seznamu (pokud není shoda 100%)
    shody = difflib.get_close_matches(vstup_uzivatele, lista_nazvu, n=1, cutoff=0.6)
    
    if shody:
        nejlepsi_shoda = shody[0]
        # Pokud se vstup liší od nalezené shody (např. překlep "Mleko" vs "Mléko polotučné")
        if vstup_uzivatele.lower() != nejlepsi_shoda.lower():
            # Zeptá se uživatele, jestli myslel tu opravu
            potvrzeni = questionary.confirm(
                f"Nenašel jsem '{vstup_uzivatele}'. Měli jste na mysli'{nejlepsi_shoda}'?",
                default=True
            ).ask()
            
            if potvrzeni:
                return nejlepsi_shoda
            else:
                # Uživatel trvá na svém (pravděpodobně nenajde nic, ale je to jeho volba)
                return vstup_uzivatele
        else:
            return nejlepsi_shoda
    
    return vstup_uzivatele

def generator_levne_vecere():
    """
    Vygeneruje náhodnou večeři ze tří surovin v rámci rozpočtu a zobrazí srovnání s běžnou cenou.
    """    
    while True:
        limit_vstup = input("❓ Kolik si přejete za večeři maximálně utratit? (v Kč): ")
        
        if not limit_vstup:
            print("[i][yellow]Odpověď zrušena. Návrat do menu...[/][/]\n")
            return
        
        try:
            rozpocet = float(limit_vstup.replace(',', '.'))
            if rozpocet > 0:
                print(f"Rozpočet {rozpocet} Kč byl nastaven.")
                break
            else:
                print("[red][i]Zadejte prosím kladnou částku![/][/]\n")
        except ValueError:
            print("[red][i]Zadejte prosím platné číslo![/][/]\n")
    

    hlavni_chod = []
    prilohy = []
    zelenina = []

    with open(CESTA_DATABAZE, mode='r', encoding='utf-8') as soubor:
        ctenar = csv.DictReader(soubor, delimiter=';')
        for radek in ctenar:
            kat = radek['kategorie']
            if "Maso" in kat or "Uzeniny" in kat:
                hlavni_chod.append(radek)
            elif "Těstoviny" in kat or "Pečivo" in kat or "Přílohy" in kat:
                prilohy.append(radek)
            elif "Zelenina" in kat or "Ovoce" in kat:
                zelenina.append(radek)

    if hlavni_chod and prilohy and zelenina:
        nasel_jsem = False
        s1, s2, s3 = None, None, None
        cena_akce_celkem = 0
        cena_bezna_celkem = 0
        
        for _ in range(100):
            s1 = random.choice(hlavni_chod)
            s2 = random.choice(prilohy)
            s3 = random.choice(zelenina)
            
            cena_akce_celkem = float(s1['cena_akce']) + float(s2['cena_akce']) + float(s3['cena_akce'])    
            if cena_akce_celkem <= rozpocet:
                cena_bezna_celkem = float(s1['cena_bezna']) + float(s2['cena_bezna']) + float(s3['cena_bezna'])
                nasel_jsem = True
                break
          
        if nasel_jsem:
            uspora = cena_bezna_celkem - cena_akce_celkem
            procento_slevy = (uspora / cena_bezna_celkem) * 100

            obsah = (
                f"\n🛒 [bold]Váš nákup do limitu {rozpocet} Kč:[/]\n\n"
                f"🥩 {s1['nazev']} ({s1['obchod']})\n"
                f"   [green]{s1['cena_akce']} Kč[/] [dim](běžně {s1['cena_bezna']} Kč)[/]\n"
                f"🍝 {s2['nazev']} ({s2['obchod']})\n"
                f"   [green]{s2['cena_akce']} Kč[/] [dim](běžně {s2['cena_bezna']} Kč)[/]\n"
                f"🥦 {s3['nazev']} ({s3['obchod']})\n"
                f"   [green]{s3['cena_akce']} Kč[/] [dim](běžně {s3['cena_bezna']} Kč)[/]\n\n"
                f"--------------------------------------\n"
                f"💰 [bold yellow]Akční cena celkem:  {cena_akce_celkem:.2f} Kč[/]\n"
                f"⚖️ [dim] Běžná cena celkem:  {cena_bezna_celkem:.2f} Kč[/]\n"
                f"🎉 [bold yellow]Ušetříte:           {uspora:.2f} Kč ({procento_slevy:.0f}%)[/]\n"
                f"💵 [dim]Na konci nákupu vám zbyde: [/][bold green]{rozpocet-cena_akce_celkem:.2f} Kč[/]"
            )
            console.print(Panel(obsah, title="🍴 Rozpočtová večeře", border_style="magenta", expand=False))
        else:
            console.print(f"[yellow]Bohužel se nepodařilo poskládat večeři do {rozpocet} Kč.[/yellow]")
    else:
        console.print("[red]Chybí data v kategoriích.[/red]")
        
def muj_nakupni_seznam():
    zaloha_seznamu = None
    
    while True:
        radky = []
        if os.path.exists(CESTA_SEZNAMU):
            with open(CESTA_SEZNAMU, "r", encoding="utf-8") as s:
                radky = [line.strip() for line in s.readlines() if line.strip()]

        text_panelu = "\n".join(radky) if radky else "[dim]Seznam je prázdný...[/]"
        
        console.clear()
        console.print(Panel(
            text_panelu,
            title="📝 [b][magenta]MŮJ NÁKUPNÍ SEZNAM[/][/]",
            subtitle="[dim]nakupni_seznam.txt[/]",
            border_style="cyan",
            padding=(1, 2)
        ))

        moznosti = [
            "➕ Přidat produkt",
            "✏️  Upravit položku",
            "🧹 Odebrat jednu položku",
            "✅ Režim odškrtávání (Checklist)",
            "🗑️  Vymazat celý seznam",
            "💾 Uložit a odejít"
        ]

        if zaloha_seznamu is not None:
            moznosti.insert(5, "↩️  ZPĚT (Vrátit smazání)")

        akce = questionary.select(
            "",
            choices=moznosti,
            pointer='👉',
            instruction=' ',
            qmark='',
            style=questionary.Style([('highlighted', 'fg:cyan bold')])
        ).ask()

        if akce == "➕ Přidat produkt":
            nazev = questionary.text("Název produktu:",
                                     qmark='❓'
                                     ).ask()
            
            if nazev:
                vybrane_parametry = questionary.checkbox(
                    "Vyberte parametry: ",
                    choices=[
                        "Cena",
                        "Množství",
                        "Obchod",
                        "Kategorie"
                    ],
                    pointer='➤ ',
                    qmark='❓',
                    instruction='(MEZERNÍK = označit, A = označit vše, ENTER = potvrdit)',
                    style=questionary.Style([
                        ('highlighted', 'fg:yellow'),
                        ('instruction', 'fg:gray italic'),
                        ('pointer', 'fg:yellow')])
                ).ask()

                detailni_info = []
                
                if vybrane_parametry:
                    for param in vybrane_parametry:
                        hodnota = questionary.text(
                            f"Zadejte hodnotu pro '{param}':",
                            qmark='❓',
                            instruction=' '
                            ).ask()
                        if hodnota:
                            detailni_info.append(f"{param}: {hodnota}")
                
                novy_radek = f"● {nazev.capitalize()}"
                if detailni_info:
                    novy_radek += f" ({', '.join(detailni_info)})"

                with open(CESTA_SEZNAMU, "a", encoding="utf-8") as s:
                    s.write(novy_radek + "\n")

        elif akce == "✏️  Upravit položku":
            if not radky:
                continue
                
            vybrany_radek = questionary.select(
                "Kterou položku chcete upravit?",
                choices=radky + ["❌ Zrušit"],
                pointer='➤ ',
                qmark='❓',
                instruction=' ',
                style=questionary.Style([
                    ('highlighted', 'fg:yellow'),
                    ('pointer', 'fg:yellow')
                    ])
            ).ask()
            
            if vybrany_radek and vybrany_radek != "❌ Zrušit":
                index = radky.index(vybrany_radek)
                novy_text = questionary.text(
                    "Upravte text:",
                    qmark='❓',
                    default=vybrany_radek.replace("● ", "")
                ).ask()
                
                if not novy_text.startswith("● "):
                    novy_text = f"● {novy_text}"
                
                radky[index] = novy_text
                
                with open(CESTA_SEZNAMU, "w", encoding="utf-8") as s:
                    s.write("\n".join(radky) + "\n")

        elif akce == "🧹 Odebrat jednu položku":
            if not radky:
                continue

            k_smazani = questionary.select(
                "Vyberte položku, kterou chcete smazat:",
                pointer='➤ ',
                qmark='❓',
                instruction=' ',
                style=questionary.Style([
                    ('highlighted', 'fg:yellow'),
                    ('pointer', 'fg:yellow')
                    ]),
                choices=radky + ["❌ Zrušit"]
            ).ask()

            if k_smazani and k_smazani != "❌ Zrušit":
                radky.remove(k_smazani)
                with open(CESTA_SEZNAMU, "w", encoding="utf-8") as s:
                    s.write("\n".join(radky) + "\n")

        elif akce == "✅ Režim odškrtávání (Checklist)":
            if not radky:
                continue

            volby_checklist = []
            for i, radek in enumerate(radky):
                je_hotovo = "[s]" in radek
                cisty_text = radek.replace("[dim][s]", "").replace("[/s][/dim]", "").replace("✅ ", "").replace("● ", "")
                volby_checklist.append(questionary.Choice(cisty_text, value=i, checked=je_hotovo))

            vybrane_indexy = questionary.checkbox(
                "Označte zakoupené položky:",
                choices=volby_checklist,
                qmark='❓',
                pointer='➤ ',
                instruction='(MEZERNÍK = označit, A = označit vše, ENTER = uložit)',
                style=questionary.Style([
                    ('highlighted', 'fg:yellow'),
                    ('pointer', 'fg:yellow'),
                    ('instruction', 'fg:gray italic')
                ])
            ).ask()

            if vybrane_indexy is not None:
                for i in range(len(radky)):
                    puvodni_text = radky[i].replace("[dim][s]", "").replace("[/s][/dim]", "").replace("✅ ", "").replace("● ", "")
                    
                    if i in vybrane_indexy:
                        radky[i] = f"[dim][s]✅ {puvodni_text}[/s][/dim]"
                    else:
                        radky[i] = f"● {puvodni_text}"

                with open(CESTA_SEZNAMU, "w", encoding="utf-8") as s:
                    s.write("\n".join(radky) + "\n")

        elif akce == "🗑️  Vymazat celý seznam":
            if radky:
                if questionary.confirm("Opravdu smazat vše?",
                                       instruction='(Enter pro potvrzení)',
                                       qmark='❓'
                                       ).ask():
                    zaloha_seznamu = radky.copy()
                    with open(CESTA_SEZNAMU, "w", encoding="utf-8") as s:
                        s.write("")
                    console.print("[yellow]Seznam smazán. Možnost 'ZPĚT' je nyní aktivní.[/]")
                    time.sleep(1)

        elif akce == "↩️  ZPĚT (Vrátit smazání)":
            if zaloha_seznamu:
                with open(CESTA_SEZNAMU, "w", encoding="utf-8") as s:
                    s.write("\n".join(zaloha_seznamu) + "\n")
                zaloha_seznamu = None
                console.print("[green]Seznam byl úspěšně obnoven![/]")
                time.sleep(1)

        elif akce == "💾 Uložit a odejít":
            console.clear()
            break
    
    
# --------------------------------------------|HLAVNÍ BĚH PROGRAMU|-------------------------------------------------------
def program():
    
    uvodni_obrazovka()
    
    datum_svatek()

    # Výběr z možností
    while True:
        
        prikaz = "[#ffffff]Vyberte si jednu z nabízených možností:[/]"
        print(Panel(
            prikaz,
            box = DOUBLE,
            border_style="#00ffff",
            expand=False,
            padding=(0,8),
            subtitle='[dim][i](Používejte šipky)[/][/]'
            ))
        
        volba = questionary.select(
            '',
            choices=[
                questionary.Choice("🔍 Vyhledat produkt podle názvu ", value="Vyhledat produkt podle názvu"),
                questionary.Choice("⚔️  Souboj obchodů ", value="Souboj obchodů"),
                questionary.Choice("🍽️  Generátor levné večeře ", value="Generátor levné večeře"),
                questionary.Choice("📝 Můj nákupní seznam ", value="Můj nákupní seznam"),
                questionary.Choice("❌ Konec ", value="Konec"),
            ],
            instruction=' ',
            pointer='👉', # ➤
            qmark='',
            style=questionary.Style([
                ('instruction', 'fg:#888888 italic'),
                ('highlighted', 'fg:gold bold'), 
                ('question', 'fg:#00AEFF bold'),
                ('pointer', 'fg:#ff8800 bold'),
                ('answer', 'fg:#00ffff bold underline')
            ])
        ).ask()

        # Volání funkcí
        if volba == "Vyhledat produkt podle názvu": 
            vyhledat_pr_podl_nazvu()
            
        elif volba == "Souboj obchodů":         
            souboj_obchodu()

        elif volba == "Generátor levné večeře":
            generator_levne_vecere()

        elif volba == "Můj nákupní seznam":
            muj_nakupni_seznam()
        
        elif volba == "Konec":
            console.print("[bold red]Ukončuji program. Na shledanou![/] 👋")
            sys.exit()
            
if __name__ == "__main__":
    program()