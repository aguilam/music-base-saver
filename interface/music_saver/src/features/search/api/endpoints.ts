import { client } from "~/shared/api/client";
import { SearchResult } from "../model/types";

export async function librarySearch(query: string, offset: number) {
    const encoded = encodeURI(query)
    const result = await client.get(`/search/library?query=${encoded}&track_offset=${offset}&album_offset=${offset}&artist_offset=${offset}`).json<SearchResult>()
    return result
}

export async function externalSearch(query: string) {
    const encoded = encodeURI(query)
    const result = await client.get(`/search/external?query=${encoded}`).json<SearchResult>()
    return result
}