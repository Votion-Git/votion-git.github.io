import pandas as pd # Data Handling and Manipulation
import requests # URL Data Requests
import time # Time Intervals for Rate Limiting Requests
import numpy as np # Better Math 
from bs4 import BeautifulSoup # HTML Processing and Parsing


genre_list_url= 'https://everynoise.com/everynoise1d.cgi?scope=all'
genre_list_response = requests.get(genre_list_url)
genre_list_content = genre_list_response.content
genre_list_soup = BeautifulSoup(genre_list_content, 'lxml')
genre_table = genre_list_soup.find('table')


genres_formatted = []
for item in genre_table.find_all('td', class_='note'):
	genre = item.text
	if genre.isnumeric():
		continue
	else:
		fixed_genre = ''.join([char for char in genre if char.isalnum()])
		genres_formatted.append(fixed_genre)


tunnel_url_txt = 'https://everynoise.com/engenremap-{}.html'
genre_tunnels = {}
for genre in genres_formatted:
	tunnel_url = tunnel_url_txt.format(genre)
	tunnel_response = requests.get(tunnel_url)
	tunnel_content = tunnel_response.content
	tunnel_soup = BeautifulSoup(tunnel_content, 'lxml')

	canvas = tunnel_soup.find_all('div', {'class':'canvas'})[1]
	genre_divs = canvas.find_all('div')
	genre_hexColors = [div.get("style").split(":")[1].split(";")[0].replace('#', '').strip() for div in genre_divs]
	genre_tunnels[genre] = genre_hexColors

genre_colorsTable = pd.DataFrame.from_dict(genre_tunnels, orient='index')
display(genre_colorsTable)
genre_colorsTable.to_csv("./genre_colors.csv")

