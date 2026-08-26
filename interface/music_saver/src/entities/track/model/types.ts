import { ShortArtist } from "~/entities/artists"
import { ShortLyrics } from "~/entities/lyrics"
import { ShortMusicVideo } from "~/entities/music-video"

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

export interface FullTrack {
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
    lyrics: ShortLyrics[]
    musicVideos: ShortMusicVideo[]
}