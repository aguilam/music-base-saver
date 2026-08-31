import { client } from "~/shared/api/client";
import { ApiKey } from "../model/types";

export async function getApiKeys() {
    const apiKeys = await client.get(`/api-keys`).json<ApiKey[]>()
    return apiKeys
}

export async function postApiKey() {
    const apiKey = await client.post(`/api-keys`).json<ApiKey>()
    return apiKey
}

export async function deleteApiKey(id: number) {
    await client.delete(`/api-keys/${id}`)
}