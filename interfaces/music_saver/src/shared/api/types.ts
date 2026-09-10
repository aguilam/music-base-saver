export interface CursorResponse<T> {
    items: T
    nextCursor: string | null
    hasMore: boolean
}