import { Show } from "solid-js";
import { deleteApiKeyMutation } from "../api/queries";
import { ApiKey } from "../model/types";
import { Button } from "~/components/ui/button";

interface ApiKeyCardProps {
    apiKey: ApiKey;
}

const ApiKeyCard = (props: ApiKeyCardProps) => {
    const apiKeyMutation = deleteApiKeyMutation()
    const handleApiKeyDelete = () => {
        apiKeyMutation.mutate(props.apiKey.id)
    }
    return (
        <div class=" flex justify-between bg-gray-600 mx-2 p-3">
            <p class={`${props.apiKey.revoked ? " line-through" : ""}`}>{props.apiKey.key}</p>
            <Show when={!props.apiKey.revoked}>
                <Button onclick={handleApiKeyDelete}>Revoke key</Button>
            </Show>
        </div>
    );
};
  
export default ApiKeyCard;