import { createMutation, createQuery, useQueryClient } from "@tanstack/solid-query";
import { cancelSync, getSync, getSyncs, postSync } from "./endpoints";
import { Accessor } from "solid-js";

export function createSyncQuery(id: Accessor<string>) {

    return createQuery(() => ({
        queryKey: ["syncs",id()],
        queryFn: () => getSync(id()),
        enabled: !!id()
    }))
}

export function createSyncsQuery() {

    return createQuery(() => ({
        queryKey: ["syncs"],
        queryFn: () => getSyncs()
    }))
}

export function createPostSyncMutation() {
    const queryClient = useQueryClient()

    return createMutation(() => ({
        mutationFn: () => postSync(),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["syncs"] })
        }
    }))
}
export function createCancelSyncMutation() {
    const queryClient = useQueryClient()

    return createMutation(() => ({
        mutationFn: (id: string) => cancelSync(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["syncs"] })
        }
    }))
}