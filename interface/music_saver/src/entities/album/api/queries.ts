import { createQuery } from "@tanstack/solid-query";
import { type Accessor } from "solid-js";
import { getAlbum } from "./endpoints";

export function createAlbumQuery(id: Accessor<number>){
    return createQuery(() => ({
        queryKey: ["album",id()],
        queryFn: () => getAlbum(id())
    }))
}
