export interface SyncedLyricsLine {
    time: number,
    text: string
}

export interface ShortLyrics {
    id: number,
    language: string,
    trackId: number,
    offset: number,
    isSynced: boolean,
    syncedText: SyncedLyricsLine[] | null,
    plainText: string | null
}