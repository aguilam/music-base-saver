import { createMutation, createQuery, useQueryClient } from "@tanstack/solid-query";
import { getConfig, changeConfig } from "./endpoints";

export function createConfigQuery(){
    return createQuery(() => ({
        queryKey: ["config"],
        queryFn: () => getConfig()
    }))
}

export function changeConfigMutation() {
    const queryClient = useQueryClient()
    return createMutation(() => ({
        mutationKey: ["config"],
        mutationFn: (config: string) => changeConfig(config),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["config"] })
        }
    }))
}