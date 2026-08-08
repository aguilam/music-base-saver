export interface ServiceHealth {
    ok: boolean
    message: string
}

export interface ServiceStatus {
    tag: string
    health: ServiceHealth
}

export interface StatusResponse {
    downloaders: ServiceStatus[]
    importers: ServiceStatus[]
    scrobblers: ServiceStatus[]
    search: ServiceStatus[]
    storages: ServiceStatus[]
}