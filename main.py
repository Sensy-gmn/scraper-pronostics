import requests
from bs4 import BeautifulSoup
import json

Allsports = {"aujourdhui": "aujourdhui", "demain": "demain"}
Allsports_all_url = "https://www.sportytrader.com/pronostics/{}/"

def display_sports():
    print("Voulez-vous récupérer les pronostics d'aujourd'hui ou de demain ?")
    choice = input("1 - Aujourd'hui\n2 - Demain\n")

    if choice == "1":
        return "aujourdhui"
    elif choice == "2":
        return "demain"
    else:
        print("Choix invalide, veuillez réessayer.")
        return display_sports()

def scrap_sport(choice):
    if choice is None:
        raise ValueError("No choice provided")

    if choice in Allsports:
        urlBase = Allsports_all_url.format(choice)
    else:
        raise ValueError("Invalid choice provided")

    opposition = []
    match_number = 1
    seen_matches = set()

    while True:
        print(f"Scraping URL: {urlBase}")
        try:
            response = requests.get(urlBase)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
        except requests.RequestException as e:
            print("================================")
            print(f"Erreur lors de la récupération des données : {e}")
            break

        if response.status_code == 200:
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')

            matchs = soup.find_all(class_="pt-4 px-3 flex flex-col justify-between h-full")
            pronostics = soup.find_all(class_="text-left font-semibold")
            leagues = soup.find_all(class_="dark:text-white text-sm")
            bet_nows = soup.find_all(class_="col-span-3 flex flex-col justify-center items-center bg-white p-0.5 rounded-md")

            if not matchs:
                print("No more matches found, breaking the loop.")
                break

            it = iter(matchs)
            new_opposition = []

            for match, prono, league, bet_now in zip(it, pronostics, leagues, bet_nows):
                try:
                    opposant_1 = match.find(class_="font-semibold text-center flex dark:text-white pr-1 lea").text.strip()
                    opposant_2 = next(it).find(class_="font-semibold text-center flex dark:text-white pl-1").text.strip()

                    odd_span = bet_now.find('span')
                    next_span = odd_span.find_next('span')
                    odd_text = next_span.text.strip()
                    odd = float(odd_text) if odd_text.replace('.', '', 1).isdigit() else None

                    pronostic_text = prono.text.strip()

                    match_id = f"{opposant_1} vs {opposant_2} - {league.text.strip()}"
                    if match_id in seen_matches:
                        continue

                    match_data = {
                        "match_id": match_number,
                        "league": league.text.strip(),
                        "opposant_1": opposant_1,
                        "opposant_2": opposant_2,
                        "pronostic": pronostic_text,
                        "cotation": odd
                    }
                    new_opposition.append(match_data)
                    seen_matches.add(match_id)
                    match_number += 1
                except StopIteration:
                    print("StopIteration encountered, breaking the loop.")
                    break
                except AttributeError as e:
                    print(f"Error processing match data: {e}")
                    continue

            if not new_opposition:
                print("No new opposition found, breaking the loop.")
                break

            opposition.extend(new_opposition)
        else:
            print("================================")
            print("Erreur lors de la récupération des données, veuillez vérifier l'URL")
            break

    if len(opposition) == 0:
        print("----------------------------------")
        print("Aucun match trouvé pour ce sport")
        print("----------------------------------")
    else:
        filename = f'Prono_{choice}.json'
        try:
            with open(filename, 'w', encoding="utf-8") as f:
                json.dump(opposition, f, ensure_ascii=False)
            print("================================")
            print("Fichier JSON créé avec succès !")
        except IOError as e:
            print("================================")
            print(f"Erreur lors de la création du fichier JSON : {e}")

choice = display_sports()
scrap_sport(choice)

while True:
    print("================================")
    print("Voulez-vous scrapper d'autres pronostics ?")
    choice = input("1 - Oui\n2 - Non\n")

    if choice == "1":
        print("================================")
        
        choice = display_sports()
        scrap_sport(choice)
    else:
        print("================================")
        print("Merci d'avoir utilisé mon programme ! :)")
        break

