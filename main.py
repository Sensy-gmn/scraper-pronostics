import requests
import time
from bs4 import BeautifulSoup
from datetime import datetime
import re
import pytz
from pymongo import MongoClient
import os
from dotenv import load_dotenv


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
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
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
        print(f"Erreur lors de la récupération des données. Code de statut : {response.status_code}")
        print(f"Contenu de la réponse : {response.text[:500]}...")  
        return []

    return opposition

    
def save_data(data):
    db = get_database()
    paris_tz = pytz.timezone('Europe/Paris')
    current_date = datetime.now(paris_tz)

    matches_collection = db.matches

    inserted_count = 0
    updated_count = 0

    for sport, matches in data.items():
        for match in matches:
            match_document = {
                'scraping_date': current_date,
                'sport': sport,
                'jour': match['jour'],
                'heure': match['heure'],
                'opposant_1': match['opposant_1'],
                'opposant_2': match['opposant_2'],
                'pronostic': match['pronostic'],
                'cote': match['cote']
            }
            
            # id unique pour chaque match
            match_id = f"{match['jour']}_{match['heure']}_{match['opposant_1']}_{match['opposant_2']}"

            # update_one éviter les doublons
            result = matches_collection.update_one(
                {'_id': match_id},
                {'$set': match_document},
                upsert=True
            )

            if result.upserted_id:
                inserted_count += 1
            elif result.modified_count > 0:
                updated_count += 1

    print(f"Données sauvegardées/mises à jour dans MongoDB avec succès !")
    print(f"Nouveaux documents insérés : {inserted_count}")
    print(f"Documents mis à jour : {updated_count}")

def get_database():
    load_dotenv()
    connection_string = os.getenv('MONGODB_URI')
    client = MongoClient(connection_string)
    return client['pronostics']

def main():
    sports = ['football', 'tennis', 'basket', 'rugby', 'handball']

    all_sports_data = {}

    for sport in sports:
        print(f"Scraping data for {sport}")
        url = f"https://www.sportytrader.com/pronostics/{sport}/"
        print(f"Scraping URL: {url}")
        print("================================")
        
        html_content = scrap_sport(url)
        if html_content:
            all_sports_data[sport] = html_content
        else:
            print(f"Échec du scraping pour {sport}")
        
        time.sleep(5)  # 5 secondes entre chaquerequête

    save_data(all_sports_data)
    print("Données sauvegardées dans MongoDB avec succès !")

if __name__ == "__main__":
    main()
