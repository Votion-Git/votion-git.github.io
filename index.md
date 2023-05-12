# Playmakr -- votion-git.github.io
## Host repo for Python-based, Spotify playlist making app

Through the use of **Spotify's** API, in edition with per-genre statistics from **www.everynoiseatonce.com**, this program provides users with a simple way to construct playlists, defining them by genres and by various acoustic quality. The vast Spotify genre space is simplified using a clustering method to provide easy-to-understand, genre super-categories or "metagenre" using acoustic measures such as Valence, Energy, Instrumentalness, and Danceability users can create emotionally defined playlists.


## Site-ations
### Spotify
https://developer.spotify.com/documentation/web-api
+ Danceability 	- how suitable a track is for dancing based on a combination of musical elements including tempo, rhythm stability, beat strength, and overall regularity. A value of 0.0 is least danceable and 1.0 is most danceable.
+ Energy		- a measure from 0.0 to 1.0 and represents a perceptual measure of intensity and activity. Typically, energetic tracks feel fast, loud, and noisy. For example, death metal has high energy, while a Bach prelude scores low on the scale. Perceptual features contributing to this attribute include dynamic range, perceived loudness, timbre, onset rate, and general entropy.
+ Instrumentalness - whether a track contains no vocals. "Ooh" and "aah" sounds are treated as instrumental in this context. Rap or spoken word tracks are clearly "vocal". The closer the instrumentalness value is to 1.0, the greater likelihood the track contains no vocal content. Values above 0.5 are intended to represent instrumental tracks, but confidence is higher as the value approaches 1.0.
+ Valence - a measure from 0.0 to 1.0 describing the musical positiveness conveyed by a track. Tracks with high valence sound more positive (e.g. happy, cheerful, euphoric), while tracks with low valence sound more negative (e.g. sad, depressed, angry).

### Every Noise At Once, by Glenn Mcdonald
https://everynoise.com
+ Every Noise at Once is an ongoing attempt at an algorithmically-generated, readability-adjusted scatter-plot of the musical genre-space, based on data tracked and analyzed for more than 6,000 genre-shaped distinctions by Spotify. 

https://www.furia.com/page.cgi?type=log&id=419
+ "red is energy, green is dynamic variation, and blue is instrumentalness..." , vist the blog for furthering reading about ENAO and music in general.
