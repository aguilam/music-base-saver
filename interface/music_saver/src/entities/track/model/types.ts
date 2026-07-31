import { ShortArtist } from "~/entities/artists"

export interface ShortTrack {
    id: number
    title: string
    duration: number
    createdAt: string
    coverUri: string | null
    bpm: number | null
    trackGain: number | null
    trackPeak: number | null
    year: number | null
    externalId: string | null
    artists: ShortArtist[]
}