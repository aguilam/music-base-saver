import { Component, For } from "solid-js"
import { Button } from "~/components/ui/button"
import { createApiKeyMutation, createApiKeyQuery } from "~/entities/api-key"
import ApiKeyCard from "~/entities/api-key/ui/apiKeyCard"
import { createProviderKeyMutation, createProviderKeyQuery } from "~/entities/provider-key"
import ProviderKeyCard from "~/entities/provider-key/ui/providerKeyCard"

const SettingsPage: Component = () => {
    const apiKeyQuery = createApiKeyQuery()
    const apiKeys = () => apiKeyQuery.data;
    const providerKeyQuery = createProviderKeyQuery()
    const providerKeys = () => providerKeyQuery.data;
    const createApiMutation = createApiKeyMutation()
    const createProviderMutation = createProviderKeyMutation()
    const handleCreateApiKey = () => {
        createApiMutation.mutate()
    }
    const handleCreateProviderKey = () => {
        createProviderMutation.mutate()
    }
    return (
        <div class=" flex flex-col gap-5 m-2">
            <p>Settings</p>
            <div>
                <div class="flex justify-between items-center mb-3">
                    <p>API keys</p>
                    <Button onClick={handleCreateApiKey}>+</Button>
                </div>
                <div class=" flex flex-col gap-2">
                    <For each={apiKeys()}>
                        {(key) => <ApiKeyCard apiKey={key} />}
                    </For>
                </div>
            </div>
            <div>
                <div class="flex justify-between items-center mb-3">
                    <p>Providers keys</p>
                    <Button onClick={handleCreateProviderKey}>+</Button>
                </div>
                <div class=" flex flex-col gap-2">
                    <For each={providerKeys()}>
                        {(key) => <ProviderKeyCard providerKey={key} />}
                    </For>
                </div>
            </div>
        </div>
    )
}
export default SettingsPage
