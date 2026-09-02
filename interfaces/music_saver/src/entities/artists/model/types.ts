import { ShortAlbum } from "~/entities/album"

export interface Artist {
    id: number
    name: string
    albumsCount: number
    description: string | null
    coverUri: string | null
    externalId: string | null
    genres: string[]
    albums: ShortAlbum[]
}


export interface ShortArtist {
    id: number
    name: string
    albumsCount: number
    coverUri: string | null
    externalId: string | null
}