import { createMutation, createQuery, useQueryClient } from "@tanstack/solid-query";
import { deleteProviderKey, getProviderKeys, postProviderKey } from "./endpoints";

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
        mutationFn: () => postProviderKey(),
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