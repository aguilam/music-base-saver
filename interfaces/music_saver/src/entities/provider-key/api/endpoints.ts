import { client } from "~/shared/api/client";
import { ProviderKey } from "../model/types";

export async function getProviderKeys() {
    const ProviderKeys = await client.get(`/providers-keys`).json<ProviderKey[]>()
    return ProviderKeys
}

export async function postProviderKey(provider: string, key: string) {
    const ProviderKey = await client.post(`/providers-keys`,{json: { key: key, provider: provider}}).json<ProviderKey>()
    return ProviderKey
}

export async function changeProviderKey(id: number, provider: string, key: string) {
    const ProviderKey = await client.patch(`/providers-keys/${id}`,{json: {key: key}}).json<ProviderKey>()
    return ProviderKey
}

export async function deleteProviderKey(id: number) {
    await client.delete(`/providers-keys/${id}`)
}