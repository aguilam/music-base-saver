import { Component, createSignal, For, Show } from "solid-js";
import { Button } from "~/components/ui/button";
import ConfigInput from "~/entities/server/ui/configInput";
import { createApiKeyMutation, createApiKeyQuery } from "~/entities/api-key";
import ApiKeyCard from "~/entities/api-key/ui/apiKeyCard";
import { createProviderKeyQuery } from "~/entities/provider-key";
import NewProviderKeyForm from "~/entities/provider-key/ui/newProviderKeyForm";
import ProviderKeyCard from "~/entities/provider-key/ui/providerKeyCard";
import { user } from "~/shared/store/user";
import { createPostSyncMutation, createSyncsQuery } from "~/features/sync";
import SyncCard from "~/features/sync/ui/syncCard";
const SettingsPage: Component = () => {
  const apiKeyQuery = createApiKeyQuery();
  const apiKeys = () => apiKeyQuery.data;
  const providerKeyQuery = createProviderKeyQuery();
  const providerKeys = () => providerKeyQuery.data;
  const createApiMutation = createApiKeyMutation();
  const syncsQuery = createSyncsQuery();
  const syncs = () => syncsQuery.data;
  const createSyncMutation = createPostSyncMutation();
  const handleCreateApiKey = () => {
    createApiMutation.mutate();
  };
  const handleStartSync = () => {
    createSyncMutation.mutate();
  };
  const [isCreating, setIsCreating] = createSignal(false);
  return (
    <div class=" flex flex-col gap-5 m-2">
      <p>Settings</p>
      <div>
        <div class="flex justify-between items-center mb-3">
          <p>API keys</p>
          <Button onClick={handleCreateApiKey}>+</Button>
        </div>
        <div class=" flex flex-col gap-2">
          <For each={apiKeys()}>{(key) => <ApiKeyCard apiKey={key} />}</For>
        </div>
      </div>
      <div>
        <div class="flex justify-between items-center mb-3">
          <p>Providers keys</p>
          <Button onClick={() => setIsCreating(!isCreating())}>+</Button>
        </div>
        <div class=" flex flex-col gap-2">
          <For each={providerKeys()}>{(key) => <ProviderKeyCard providerKey={key} />}</For>
          <Show when={isCreating() == true}>
            <NewProviderKeyForm setIsChange={setIsCreating} />
          </Show>
        </div>
      </div>

      <Show when={user.role == "admin"}>
        <div>
          <div class=" flex gap-2 items-center">
            <p>Sync</p>
            <Button onClick={handleStartSync}>Start sync</Button>
          </div>
          <For each={syncs()}>{(sync) => <SyncCard sync={sync} />}</For>
        </div>
        <ConfigInput />
      </Show>
    </div>
  );
};
export default SettingsPage;
