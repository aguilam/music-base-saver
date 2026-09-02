import { createMutation, createQuery, useQueryClient } from "@tanstack/solid-query";
import { changeProviderKey, deleteProviderKey, getProviderKeys, postProviderKey } from "./endpoints";

export function createProviderKeyQuery(){
    return createQuery(() => ({
        queryKey: ["provider-keys"],
        queryFn: () => getProviderKeys()
    }))
}

export function createProviderKeyMutation(){
    const queryClient = useQueryClient()

    return createMutation(() => ({
        mutationKey: ["provider-keys"],
        mutationFn: ({provider, key}: {provider: string, key: string}) => postProviderKey(provider,key),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["provider-keys"] })
        },
    }))
}

export function changeProviderKeyMutation(){
    const queryClient = useQueryClient()

    return createMutation(() => ({
        mutationKey: ["provider-keys"],
        mutationFn: ({id, provider, key}: {id: number, provider: string, key: string}) => changeProviderKey(id,provider,key),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["provider-keys"] })
        },
    }))
}

export function deleteProviderKeyMutation(){
    const queryClient = useQueryClient()

    return createMutation(() => ({
        mutationKey: ["provider-keys"],
        mutationFn: (id: number) => deleteProviderKey(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["provider-keys"] })
          },
    }))
}