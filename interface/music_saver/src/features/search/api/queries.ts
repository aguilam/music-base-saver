import { createInfiniteQuery } from "@tanstack/solid-query";
import { externalSearch, librarySearch } from "./endpoints";

export function createLibrarySearchQuery(query: string) {
    return createInfiniteQuery(() => ({
        queryKey: ["search","library",query],
        queryFn: () => librarySearch(query,0),
        initialPageParam: 0,
        getNextPageParam: (lastPage, pages) => 0
    }))
}

export function createExternalSearchQuery(query: string) {
    return createInfiniteQuery(() => ({
        queryKey: ["search","external",query],
        queryFn: () => externalSearch(query),
        initialPageParam: 0,
        getNextPageParam: (lastPage, pages) => 0
    }))
}