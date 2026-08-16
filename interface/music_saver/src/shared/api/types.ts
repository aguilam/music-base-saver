export interface CurrentUser {
    id: number
    username: string
    role: string
}

export interface UserProfile {
    id: number
    username: string
}

export interface Track {
    id: string,
    title: string,
    artist: string,
    coverUri: string,
    externalId: string,
    length: number,
};
  
export interface Album {
    id: string,
    title: string,
    artist: string,
    trackCount: number,
    albumLength: number,
    coverUri: string,
    externalId: string,
    year: number,
};
  
export interface Artist {
    id: string,
    name: string,
    externalId: string,
    avatarUri: string,
};
  
export interface Playlist {
    id: string,
    title: string,
    coverUri: string,
};

export type ArtistWithAlbums = Artist & {
    albums: Album[];
};

export type AlbumWithTracks = Album & {
    tracks: Track[];
};

export type PlaylistWithTracks = Playlist & {
    tracks: Track[];
};

export type AllContent = {
    tracks: Track[];
    albums: Album[];
    artists: Artist[];
};