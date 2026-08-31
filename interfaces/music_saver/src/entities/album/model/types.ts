import { ShortArtist } from "~/entities/artists"
import { ShortTrack } from "~/entities/track"

export interface Album {
    id: number
    title: string
    duration: number
    tracksCount: number
    createdAt: string
    year: number | null
    description: string | null
    coverUri: string | null
    externalId: number | null
    tracks: ShortTrack[]
    artists: ShortArtist[]
    genres: string[]
    moods: string[]
}
export interface ShortAlbum{
    id: number
    title: string
    coverUri: string | null
    year: number | null
    externalId: string | null
    artists: ShortArtist[]
}
