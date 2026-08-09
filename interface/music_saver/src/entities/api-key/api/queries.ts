import { createMutation, createQuery, useQueryClient } from "@tanstack/solid-query";
import { deleteApiKey, getApiKeys, postApiKey } from "./endpoints";

export function createApiKeyQuery(){
    return createQuery(() => ({
        queryKey: ["api-keys"],
        queryFn: () => getApiKeys()
    }))
}

export function createApiKeyMutation(){
    const queryClient = useQueryClient()

    return createMutation(() => ({
        mutationKey: ["api-keys"],
        mutationFn: () => postApiKey(),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["api-keys"] })
        },
    }))
}

export function deleteApiKeyMutation(){
    const queryClient = useQueryClient()

    return createMutation(() => ({
        mutationKey: ["api-keys"],
        mutationFn: (id: number) => deleteApiKey(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["api-keys"] })
          },
    }))
}