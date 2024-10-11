import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re


def scrap_sport(url):
    #
    #Scrap de data du site SportyTrader formaté dans un JSON
    #
    #Parameters:
    #url (str): L'URL du site à scraper
    #
    #Returns:
    #list: objets contenant pronostics des matchs
    #

    opposition = []
    match_number = 1
    seen_matches = set()

    print(f"Scraping URL: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
    except requests.RequestException as e:
        print("================================")
        print(f"Erreur lors de la récupération des données : {e}")
        return []

    if response.status_code == 200:
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

        #
        # Récupére les containers des matchs, pronostics, ligues, dates et bet_nows
        #
        matchs = soup.find_all(class_="pt-4 px-3 flex flex-col justify-between h-full")
        pronostics = soup.find_all(class_="text-left font-semibold")
        date = soup.find_all(class_="dark:text-white font-bold")
        leagues = soup.find_all(class_="dark:text-white text-sm")
        bet_nows = soup.find_all(class_="col-span-3 flex flex-col justify-center items-center bg-white p-0.5 rounded-md")

        if not matchs:
            print("Aucun match trouvé")
            return []

        it = iter(matchs)
        new_opposition = []


        # Boucle qui itère sur éléments des matchs, pronostics, ligues, dates et bet_nows
        # extrait informations nécessaires pour chaque match et stocke dans une liste
        for match, prono, league, date, bet_now in zip(it, pronostics, leagues, date, bet_nows):
            try:
                
                date_text = date.text.strip()
                date_obj = datetime.strptime(date_text, "%d %b. %Y - %H:%M")
                jour = date_obj.strftime('%d/%m/%Y')
                heure = date_obj.strftime('%Hh%M')

                opposant_1 = match.find(class_="font-semibold text-center flex dark:text-white pr-1 lea").text.strip()
                opposant_2 = match.find_next(class_="font-semibold text-center flex dark:text-white pl-1").text.strip()
                odd_span = bet_now.find('span')
                next_span = odd_span.find_next('span')
                odd_text = next_span.text.strip()
                odd = float(odd_text) if odd_text.replace('.', '', 1).isdigit() else None

                pronostic_text = prono.text.strip()
                league_text = league.text.strip()
                league_text = re.sub(r'\s+', ' ', league_text)

                match_id = f"{opposant_1} vs {opposant_2} - {league_text}"
                if match_id in seen_matches:
                    continue

                match_data = {
                    "match_id": match_number,
                    "league": league_text,
                    "jour": jour,
                    "heure": heure,
                    "opposant_1": opposant_1,
                    "opposant_2": opposant_2,
                    "pronostic": pronostic_text,
                    "cote": odd,
                }

                new_opposition.append(match_data)
                seen_matches.add(match_id)
                match_number += 1


            except StopIteration:
                print("Aucun match trouvé")
                break
            except AttributeError as e:
                print(f"Error processing match data: {e}")
                continue

        if not new_opposition:
            print("Aucun match trouvé")
            return []

        opposition.extend(new_opposition)
    else:
        print("================================")
        print("Erreur lors de la récupération des données, veuillez vérifier l'URL")
        return []

    return opposition

    
def save_data(data):
    #
    # Obtenir la date actuelle
    #
    # Crée un nom de fichier avec la date
    #
    # Sauvegarder les données dans le fichier
    #
    current_date = datetime.now().strftime("%Y-%m-%d") 
    filename = f"pronostics_{current_date}.json"

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def main():
    sports_urls = {
        "football": "https://www.sportytrader.com/pronostics/football/",
        "tennis": "https://www.sportytrader.com/pronostics/tennis/",
        "basket": "https://www.sportytrader.com/pronostics/basket/",
        "rugby": "https://www.sportytrader.com/pronostics/rugby/",
        "handball": "https://www.sportytrader.com/pronostics/handball/",
    }

    all_sports_data = {}

    for sport, url in sports_urls.items():
        print(f"Scraping data for {sport}")
        sport_data = scrap_sport(url)
        if sport_data:
            all_sports_data[sport] = sport_data

    save_data(all_sports_data)
    print("Fichier JSON créé avec succès !")

if __name__ == "__main__":
    main()

