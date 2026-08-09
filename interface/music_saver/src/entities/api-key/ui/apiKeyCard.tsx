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
            <p>{props.apiKey.key}</p>
			<Button onclick={handleApiKeyDelete}>Revoke key</Button>
        </div>
    );
};
  
export default ApiKeyCard;