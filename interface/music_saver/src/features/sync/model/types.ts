export interface UnboundFiles {
    covers: [string,string][]
    lyrics: [string,string][]
    videos: [string,string][]
}

export interface SyncMetric {
    searched_new: number
    processed: number
    added: number
    deleted: number
}

export interface SyncResult {
    tracks: SyncMetric
    covers: SyncMetric
    lyrics: SyncMetric
    videos: SyncMetric
    unbound_files: UnboundFiles
}

export interface Sync {
    id: string
    result: SyncResult
    progress: number
    status: string
    error: string
}
