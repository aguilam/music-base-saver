import { client } from "~/shared/api/client";
import { ProviderKey } from "../model/types";

export async function getProviderKeys() {
    const ProviderKeys = await client.get(`/providers-keys`).json<ProviderKey[]>()
    return ProviderKeys
}

export async function postProviderKey() {
    const ProviderKey = await client.post(`/providers-keys`).json<ProviderKey>()
    return ProviderKey
}

export async function deleteProviderKey(id: number) {
    await client.delete(`/providers-keys/${id}`)
}