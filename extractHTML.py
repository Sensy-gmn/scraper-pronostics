import requests
from bs4 import BeautifulSoup

urlBase = "https://www.sportytrader.com/pronostics/"

response = requests.get(urlBase)
response.encoding = response.apparent_encoding

if response.status_code == 200:
  html = response.text
  soup = BeautifulSoup(html, 'html.parser')

  f = open('aScraper.html', 'w', encoding = response.encoding)

  f.write(soup.prettify())

  f.close()