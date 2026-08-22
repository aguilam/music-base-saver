import { ShortAlbum } from "~/entities/album";
import { ShortArtist } from "~/entities/artists";
import { ShortTrack } from "~/entities/track";

export interface SearchResult {
    artists: ShortArtist[]
    albums: ShortAlbum[]
    tracks: ShortTrack[]
}