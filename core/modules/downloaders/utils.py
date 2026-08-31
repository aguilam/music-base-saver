def compare_tracks(original_metadata: dict, track_metadata: dict) -> float:
    similarity = 0.0
    if any(
        orig.lower() in track.lower()
        for orig in original_metadata["title"]
        for track in track_metadata["title"]
    ):
        similarity += 0.5
    if any(
        orig.lower() in track.lower()
        for orig in original_metadata["artist"]
        for track in track_metadata["artist"]
    ):
        similarity += 0.35
    if track_metadata["length"] in original_metadata["length"]:
        similarity += 0.15
    return similarity


def find_best_track(
    searched_tracks: list[Track],
) -> dict[str, list]:
    frequent_title: list[list] = []
    frequent_artists: list[list] = []
    frequent_length = []
    for track in searched_tracks:
        title_added = False
        for artist in track.artists:
            artist_added = False
            for i in range(0, len(frequent_artists)):
                if frequent_artists[i][0].lower() == artist.name.lower():
                    frequent_artists[i].append(artist.name.lower())
                    artist_added = True
                    break
            if not artist_added:
                frequent_artists.append([artist.name.lower()])
        for i in range(0, len(frequent_title)):
            if frequent_title[i][0].lower() == track.title.lower():
                frequent_title[i].append(track.title.lower())
                title_added = True
                break
        if not title_added:
            frequent_title.append([track.title.lower()])
        frequent_length.append(track.length)
    best_match_title = list(
        sorted(frequent_title, key=lambda titles: len(titles), reverse=True)
    )
    best_match_artist = list(
        sorted(frequent_artists, key=lambda artists: len(artists), reverse=True)
    )
    track = []
    for t in best_match_title[:5]:
        track.append(t[0])
    artist = []
    for a in best_match_artist[:5]:
        artist.append(a[0])
    best_match_track = {"title": track, "artist": artist, "length": frequent_length}
    return best_match_track
