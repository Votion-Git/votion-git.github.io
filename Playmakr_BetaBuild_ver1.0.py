# CODE BREAKDOWN 

# Playmakr is a python script that accesses a user's Spotify library,
# sorts all of the tracks found in both playlists and 'Liked Songs'.
# It does this by first, analysing each track's associated genre and,
# using data pulled from www.everynoiseatonce.com assignin each track
# to a user defined 'metagenre'. After doing so, the program then asks
# for each desired playlists' criteria; metagenres to include, and 
# 'seeds' for various qualitative acoustic measures ('QA scores') read from Spotify
# metadata. The last of the code takes each playlists' track list and
# saves them to the user's library.

# PYTHON LIBRARIES

import pandas as pd # Data Handling and Manipulation
import requests # URL Data Requests
import time # Time Intervals for Rate Limiting Requests
import numpy as np # Math
from bs4 import BeautifulSoup # HTML Processing and Parsing
import spotipy # Python Spotify Library
from spotipy.oauth2 import SpotifyOAuth # Spotify API Interactions
import configparser # For Getting Client ID and Secret
from collections import Counter # Counter for Cluster Reduction

# Step 1 - Getting Track and Genre Data, from Spotify and ENAO **********

# - 1.1 Functions

def hex_to_rgb(hex): # converts alphanumeric RGB hex codes to 0-255 numeric ranges
	return [int(hex[i:i+2], 16) for i in (0, 2, 4)]

# - 1.2 Code

# reading API Client ID and Secret from config file
config = configparser.ConfigParser()
config.read('config.txt')
client_id = config['Section1']['client_id']
client_secret = config['Section1']['client_secret']
redirect_url = config['Section1']['redirect_url']
scope = "playlist-read-private, playlist-read-collaborative, user-library-read, playlist-modify-public, playlist-modify-private"

# authorizing with API
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
	client_id=client_id, client_secret=client_secret, redirect_uri=redirect_url, 
	scope=scope))

# getting track information from playlists
all_tracks = []
playlists = sp.current_user_playlists()
for playlist in playlists['items']:
	playlist_id = playlist['id']
	playlist_name = playlist['name']

	# get tracks from playlist
	tracks = sp.playlist_tracks(playlist_id, fields='items(track(id, artists(id)))')['items']

	# add tracks to list
	for track in tracks:
		track_info = track['track']
		track_id = track_info['id']
		artist_id = [artist['id'] for artist in track_info['artists']][0]

		# get track features and metadata
		track_features = sp.audio_features(track_id)[0]
		track_genres = sp.artist(artist_id)['genres']

		# add all track information to list
		all_tracks.append({'track id': track_id, 'danceability': track_features['danceability'],
						'energy': track_features['energy'], 'acousticness': track_features['acousticness'],
						'valence': track_features['valence'], 'genres': track_genres})

# getting track information from liked songs
liked_songs = sp.current_user_saved_tracks()
for song in liked_songs['items']:
	track_info = song['track']
	track_id = track_info['id']
	artist_id = [artist['id'] for artist in track_info['artists']][0]

	# get track features and metadata
	track_features = sp.audio_features(track_id)[0]
	track_genres = sp.artist(artist_id)['genres']

	# add all track information to list
	all_tracks.append({'track id': track_id, 'danceability': track_features['danceability'],
					'energy': track_features['energy'], 'acousticness': track_features['acousticness'],
					'valence': track_features['valence'], 'genres': track_genres})

# pandas dataframe of each track and its respective genre and track QA scores
user_track_data = pd.DataFrame(all_tracks, columns=['track id', 'danceability', 'energy', 'acousticness', 'valence', 'genres'])
user_track_data.drop_duplicates(subset='track id', inplace=True, ignore_index=True)

# this list will ensure only relevant genre are used in upcoming calculations, instead of all genre
user_genres = user_track_data['genres'].explode().drop_duplicates().to_list()

# fetching ENAO genre data for relevant genre
url = 'http://everynoise.com/engenremap.html'
response = requests.get(url)
html_content = response.content
soup = BeautifulSoup(html_content, 'html.parser')

cleaned_data = {}
genres = []
color_values = []
y_coords = []
x_coords = []

# reading html for each genre's x and y positions, as well as its rgb color hex
for item in soup.find_all("div", scan="true"):
	onclick_element = item.get('onclick')
	genre = onclick_element.split(',')
	genres.append(genre[1].strip().strip('\"'))
	
	style_element = item.get('style')
	color_and_coords = style_element.split(';')
	color = color_and_coords[0].strip().strip('\"')
	color_hex = color.split('#')
	color_values.append(hex_to_rgb(color_hex[1]))
	
	y_coords.append(int(color_and_coords[1].strip().strip('\"').strip('top: ').strip('px')))
	x_coords.append(int(color_and_coords[2].strip().strip('\"').strip('left: ').strip('px')))
	time.sleep(.0001)

cleaned_data['Genres'] = genres
cleaned_data['Y Coords'] = y_coords
cleaned_data['X Coords'] = x_coords
cleaned_data['Color Values'] = color_values

# pandas dataframe of genre data from ENAO
genre_data = pd.DataFrame(data=cleaned_data)
genre_data = genre_data.astype({'Y Coords': 'Int64', 'X Coords': 'Int64'})

# these values are necessary for constructing the similarity matrix
genres = [genre for genre in genres if genre in user_genres]

# calulates the maximum values for both measures
two_dMax = (((max(x_coords))**2) + ((max(y_coords))**2))**0.5
three_dMax = 255*(np.sqrt(3))


# Step 2 - Creating a Similarity Matrix and Clustering Subgenre **********

# - 2.1 Functions

def get_eucDistance(x_genre, y_genre): # calculates the Euclidean distance between genres' x and y coordinates
	xg_idx = genre_data.index[genre_data['Genres'] == x_genre].to_list()[0]
	yg_idx = genre_data.index[genre_data['Genres'] == y_genre].to_list()[0]
	
	xg_xCoord = genre_data.at[xg_idx, 'X Coords']
	yg_xCoord = genre_data.at[yg_idx, 'X Coords']
	
	xg_yCoord = genre_data.at[xg_idx, 'Y Coords']
	yg_yCoord = genre_data.at[yg_idx, 'Y Coords']
	
	dist = (((xg_xCoord - yg_xCoord)**2) + ((xg_yCoord - yg_yCoord)**2))**0.5
	return dist

def get_rgbDistance(x_genre, y_genre): # calcuates 3D Euclidean distance using RGB values as x, y, and z coordinates
	xg_idx = genre_data.index[genre_data['Genres'] == x_genre].to_list()[0]
	yg_idx = genre_data.index[genre_data['Genres'] == y_genre].to_list()[0]
	
	xg_rgb = genre_data.at[xg_idx, 'Color Values']
	yg_rgb = genre_data.at[yg_idx, 'Color Values']
	
	dist = (((xg_rgb[0] - yg_rgb[0])**2) + ((xg_rgb[1] - yg_rgb[1])**2) + ((xg_rgb[2] - yg_rgb[2])**2))**0.5
	return dist

def calculate_distance(x_genre): # combines the two distance calculations into one similarity measurement
    distance_row = []
    x_index = genres.index(x_genre)
    for i, y_genre in enumerate(genres): # each genre is compared to all others
        if i > x_index:
            break
        distance = 0.5*((get_eucDistance(x_genre, y_genre)/two_dMax) + (get_rgbDistance(x_genre, y_genre)/three_dMax))
        distance_row.append(distance)
    return distance_row

def get_closest_items(current_matrix): # finds current matrix's closest clusters
	items = []
	item_1 = current_matrix.min().idxmin()
	item_2 = current_matrix[item_1].idxmin()
	items.extend(item_1)
	items.extend(item_2)
	return [item_1, item_2]

def calc_cluster_values(current_matrix, items): # creates new column for cluster, averaging their values together
	item1_label = items[0]
	item2_label = items[1]
	
	joined_column = current_matrix[[item1_label, item2_label]].mean(axis=1)
	return joined_column

def new_cluster_name(items): # generates new name for cluster, a string of each subgenre contained
	name = ', '.join(items)
	return str(name)

def remove_individuals(current_matrix, items): # removes the two clusters that formed the cluster including them
	item1_label = items[0]
	item2_label = items[1]
	
	new_matrix = current_matrix.drop(index=items).drop(columns=items)
	return new_matrix

def metagenre_correction(clusters): # takes in user input to identify 'metagenre' and/or join clusters if deemed necessary
	start_txt = "Currently there are {} identified metagenres containing a range of {}-{} subgenres within."
	metagenre_count = len(clusters)
	subgenre_count_min = min([len(count) for count in clusters])
	subgenre_count_max = max([len(count) for count in clusters])
	print(start_txt.format(metagenre_count, subgenre_count_min, subgenre_count_max))
	print('\n')
	renamed_clusters = {}
	for cluster in clusters:
		during_txt = "Current metagenres: {}\n\n"
		print(during_txt.format(renamed_clusters.keys()))
		words = []
		for genre in cluster:
			word = genre.split()
			words.extend(word)
		counts = Counter(words) # clusters are displayed as values counts where each value is a single word that occurs in the cluster
		print(counts)
		metagenre = input("\nWhat should this cluster be called: ")
		if metagenre in renamed_clusters.keys():
			clustered = renamed_clusters[metagenre]
			clustered.extend(cluster)
			renamed_clusters[metagenre] = clustered
		else:
			renamed_clusters[metagenre] = cluster
	return renamed_clusters

def rewrite_track_genres(current_genre_column, metagenre_dict): # identifies the first subgenre of each track and uses it to deterimine 'metagenre'
	new_genre_column = []
	current_genre_column.fillna(value=0)
	for genre_list in current_genre_column:
		if isinstance(genre_list, list):
			old_genre = genre_list[0]
			for metagenre, subgenres in metagenre_dict.items():
				if old_genre in subgenres:
					new_genre_column.append(metagenre)
				else:
					continue
		else:
			new_genre_column.append('unspecified')

	return new_genre_column

# - 2.2 Code

# calculates initial matrix, which is each genre's distance to all others
distance_rows = []

for genre in genres: # only adds relevant genres to matrix
	distance_rows.append(calculate_distance(genre))

# half-matrix is calculated and then mirrored
initial_matrix = pd.DataFrame(distance_rows, index=genres, columns=genres)
diag = np.equal(*np.indices(initial_matrix.shape))
half_matrix = initial_matrix.mask(diag).fillna(0).infer_objects()
bottom_half = half_matrix[half_matrix >0]
top_half = bottom_half.T
distance_matrix = bottom_half.fillna(top_half)

# this value is used to stop the clustering, indicates the lowest degree of similarity two clusters can have 
threshold = 0.085

# loops over the initial matrix, finding the two closest clusters, combining their columns and rows
while distance_matrix.min().min() < threshold:
	items = get_closest_items(distance_matrix)
	name = new_cluster_name(items)

	new_cluster = calc_cluster_values(distance_matrix, items)
	distance_matrix[name] = new_cluster
	distance_matrix.loc[name] = new_cluster
	distance_matrix = remove_individuals(distance_matrix, items)

# the product of the loop is a list of lists
clusters = []
# each sublist being all the subgenre belonging to a cluster and therefore, a 'metagenre'
for cluster in distance_matrix.columns.to_list():
	cluster_genres = cluster.split(', ')
	clusters.append(cluster_genres)

# user is presented with each cluster then determines the name for the 'metagenre' it represents
final_clusters = metagenre_correction(clusters)

# adding an additional column to the dataframe of track data, denoting each tracks 'metagenre'
new_genre_column = rewrite_track_genres(user_track_data['genres'], final_clusters)
user_track_data['metagenres'] = new_genre_column


# Step 3 - Getting Criteria for Playlists **********

# - 3.1 Functions

def playlist_criteria(metagenres_names): # accepts user input for as many playlists as the user creates
	playlists_made = {"pTitles": [], "pGenres": [], "pD_seeds": [], "pE_seeds": [], "pA_seeds": [], "pV_seeds": [] }

	while True: # initial loop
		q0 = input("\n\nEnter playlist title: ") 
		playlists_made["pTitles"].append(q0)

		q1_txt = "For playlist, \"{}\", what genres should be included?\nGENRES: {}\n"
		q1 = input(q1_txt.format(q0, metagenres_names))
		q1_genres = q1.split(', ')
		playlists_made['pGenres'].append(q1_genres)

		print("\nAnd for this playlist, what should the center values be for\n")
		q2_dan = input("Danceability: ")
		playlists_made['pD_seeds'].append(q2_dan)

		q2_ene = input("Energy: ")
		playlists_made['pE_seeds'].append(q2_ene)

		q2_aco = input("Acousticness: ")
		playlists_made['pA_seeds'].append(q2_aco)

		q2_val = input("Valence: ")
		playlists_made['pV_seeds'].append(q2_val)

		contq = input("\nDo you wish to continue? (y/n) ")
		if contq.lower() == 'n':
			break

	while True: # secondary loop in case edits to any playlist need to be made before proceeding
		print("\nCurrent playlists:")
		for i, title in enumerate(playlists_made["pTitles"]):
			print(f"{i+1}. {title}")
		editq = input("\nWhich playlist would you like to edit? Enter a number, or 'q' to quit: ")
		if editq.lower() == 'q':
			break
		elif not editq.isdigit() or int(editq) < 1 or int(editq) > len(playlists_made["pTitles"]):
			print("Invalid input. Please enter a number between 1 and ", len(playlists_made["pTitles"]))
			continue

		idx = int(editq) - 1
		q0 = input("Enter new playlist title: ")
		playlists_made["pTitles"][idx] = q0

		q1_txt = "For playlist, \"{}\", what genres should be included?\nGENRES: {}\n"
		q1 = input(q1_txt.format(q0, metagenres_names))
		q1_genres = q1.split(', ')
		playlists_made['pGenres'][idx] = q1_genres

		print("\nAnd for this playlist, what should the center values be for\n")
		q2_dan = input("Danceability: ")
		playlists_made['pD_seeds'][idx] = q2_dan

		q2_ene = input("Energy: ")
		playlists_made['pE_seeds'][idx] = q2_ene

		q2_aco = input("Acousticness: ")
		playlists_made['pA_seeds'][idx] = q2_aco

		q2_val = input("Valence: ")
		playlists_made['pA_seeds'][idx] = q2_val

	return playlists_made

def track_playlist_sorting(): # assigns tracks to best fitting playlist
	final_playlists_uris = {}
	for title in playlists['pTitles']:
		final_playlists_uris[title] = []
	used_genres = set([metagenre for pGenres in playlists['pGenres'] for metagenre in pGenres])

	for metagenre in list(used_genres):
		tracks_by_genre = user_track_data[user_track_data['metagenres'] == metagenre]
		playlists_by_genre = []
		for idx, genre_incList in enumerate(playlists['pGenres']):
			if metagenre in genre_incList:
				playlists_by_genre.append(idx)

		for i in range(len(tracks_by_genre)): # for playlists sharing any 'metagenre'
			track_uri = 'spotify:track:' + str(tracks_by_genre.iat[i, 0])
			dan_flt = tracks_by_genre.iat[i, 1]
			ene_flt = tracks_by_genre.iat[i, 2]
			aco_flt = tracks_by_genre.iat[i, 3]
			val_flt = tracks_by_genre.iat[i, 4]
			fit_score = []

			for index in playlists_by_genre:
				dan_seed = float(playlists['pD_seeds'][index])
				ene_seed = float(playlists['pE_seeds'][index])
				aco_seed = float(playlists['pA_seeds'][index])
				val_seed = float(playlists['pV_seeds'][index])
				
				# determines the closeness of the tracks QA scores to each playlists' seed values
				score = ((abs(dan_flt - dan_seed) + abs(ene_flt - ene_seed)
						+ abs(aco_flt - aco_seed) + abs(val_flt - val_seed))/4)

				fit_score.append(score)

			correct_playlist = playlists['pTitles'][playlists_by_genre[fit_score.index(min(fit_score))]]
			final_playlists_uris[correct_playlist].append(track_uri)

	return final_playlists_uris

def unspec_playlist_sorting(): # creates lists of possible 'unspecified' genre tracks per playlist
	unspec_playlists_uris = {}
	for title in playlists['pTitles']:
		unspec_playlists_uris[title] = []

	unspec_tracks = user_track_data[user_track_data['metagenres'] == 'unspecified']

	for i in range(len(unspec_tracks)):
		track_uri = 'spotify:track:' + str(unspec_tracks.iat[i, 0])
		dan_flt = unspec_tracks.iat[i, 1]
		ene_flt = unspec_tracks.iat[i, 2]
		aco_flt = unspec_tracks.iat[i, 3]
		val_flt = unspec_tracks.iat[i, 4]
		fit_score = []

		for idx, title in enumerate(playlists['pTitles']):
			dan_seed = float(playlists['pD_seeds'][idx])
			ene_seed = float(playlists['pE_seeds'][idx])
			aco_seed = float(playlists['pA_seeds'][idx])
			val_seed = float(playlists['pV_seeds'][idx])
			
			# possiblity is calculated via QA scores alone
			score = ((abs(dan_flt - dan_seed) + abs(ene_flt - ene_seed)
					+ abs(aco_flt - aco_seed) + abs(val_flt - val_seed))/4)

			fit_score.append(score)

		correct_playlist = playlists['pTitles'][fit_score.index(min(fit_score))]
		unspec_playlists_uris[correct_playlist].append(track_uri)

	return unspec_playlists_uris

# - 3.2 Code

# creates a unique list of each 'metagenre'
metagenre_names = list(set(final_clusters.keys()))

# gathers user's definitions for each playlist being made
playlists = playlist_criteria(metagenre_names)

# sorts each track based upon the definitions
finished_playlist_uris = track_playlist_sorting()

# provides a list of possible 'unspecifed' genre tracks per playlist 
unspecified_genre_uris = unspec_playlist_sorting()


# Step 4 - Uploading Playlists to Spotify **********

# - 4.1 Functions - None

# - 4.2 Code

# gets user's Spotify id
user_id = sp.me()['id']

# loops through both lists, those tracks with genre first
for title, uris in finished_playlist_uris.items():
	playlist_info = sp.user_playlist_create(user_id, title)
	playlist_id = playlist_info['id']
	sp.user_playlist_add_tracks(user_id, playlist_id, uris)
	

for title, uris in unspecified_genre_uris.items():
	unspec_title = ('Unspecified tracks for: ' + title)
	playlist_info = sp.user_playlist_create(user_id, unspec_title)
	playlist_id = playlist_info['id']
	sp.user_playlist_add_tracks(user_id, playlist_id, uris)