import { ShortTrack } from "~/entities/track"
import { ShortUser } from "~/entities/user"

export interface Playlist {
    id: number
    title: string
    isPublic: boolean
    coverUri: string | null
    owners: ShortUser[]
    tracksCount: number
    duration: number
    createdAt: string
    tracks: ShortTrack[]
}

export interface ShortPlaylist {
    id: number
    title: string
    owners: ShortUser[]
    public: boolean
    createdAt: string
    tracksCount: number
    duration: number
    coverUri: string | null
}
