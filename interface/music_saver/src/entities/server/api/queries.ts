import { createMutation, createQuery, useQuery, useQueryClient } from "@tanstack/solid-query";
import { getConfig, changeConfig, getServerStats } from "./endpoints";

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

export function createServerStatsQuery() {
    return useQuery(() => ({
        queryKey: ["server-stats"],
        queryFn: () => getServerStats()
    }))
}