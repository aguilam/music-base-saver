import { createInfiniteQuery, createQuery } from "@tanstack/solid-query";
import { type Accessor } from "solid-js";
import { getAlbum, getAlbums } from "./endpoints";

export function createAlbumsQuery() {
    return createInfiniteQuery(() => ({
        queryKey: ["albums"],
        queryFn: ({pageParam}) => getAlbums(pageParam),
        initialPageParam: null as string | null,
        getNextPageParam: (lastPage) => lastPage.hasMore ? lastPage.nextCursor : undefined,
    }))
}

export function createAlbumQuery(id: Accessor<number>){
    return createQuery(() => ({
        queryKey: ["album",id()],
        queryFn: () => getAlbum(id())
    }))
}
