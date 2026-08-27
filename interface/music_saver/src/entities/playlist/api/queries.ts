import { createMutation, createQuery, useQueryClient } from "@tanstack/solid-query";
import { Accessor } from "solid-js";
import { createPlaylist, deletePlaylist, getPlaylist, getUserPlaylists, patchPlaylist } from "./endpoints";

export function createPlaylistQuery(id: Accessor<number>){
    return createQuery(() => ({
        queryKey: ["playlist",id()],
        queryFn: () => getPlaylist(id())
    }))
}

export function createUserPlaylistsQuery(userId: Accessor<number>) {
    return createQuery(() => ({
        queryKey: ["user-playlist",userId()],
        queryFn: () => getUserPlaylists(userId())
    }))
}

export function createPlaylistMutation() {
    const queryClient = useQueryClient()

    return createMutation(() => ({
        mutationFn: (data: {title: string, trackIds: number[], ownerIds: number[], isPublic: boolean}) => createPlaylist(data.title,data.trackIds,data.ownerIds,data.isPublic),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["user-playlist"] })
        },
    }))
}

export function changePlaylistMutation() {
    const queryClient = useQueryClient()

    return createMutation(() => ({
        mutationFn: (data: {id: number, title: string | null, trackIds : number[] | null, ownerIds: number[] | null, isPublic: boolean | null}) => patchPlaylist(data.id,data.title,data.trackIds,data.ownerIds,data.isPublic),
        onSuccess: (_data,data) => {
            queryClient.invalidateQueries({ queryKey: ["user-playlist"] })
            queryClient.refetchQueries({ queryKey: ["playlist",data.id] })
        },
    }))
}

export function deletePlaylistMutation() {
    const queryClient = useQueryClient()
    return createMutation(() => ({
        mutationFn: (id: number) => deletePlaylist(id),
        onSuccess: (_data, id) => {
            queryClient.invalidateQueries({ queryKey: ["user-playlist"] })
            queryClient.invalidateQueries({ queryKey: ["playlist", id] })
        },
    }))
}