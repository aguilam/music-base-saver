import { deleteProviderKeyMutation } from "../api/queries";
import { ProviderKey } from "../model/types";
import { Button } from "~/components/ui/button";

interface ProviderKeyCardProps {
    providerKey: ProviderKey;
}

const ProviderKeyCard = (props: ProviderKeyCardProps) => {
    const providerKeyMutation = deleteProviderKeyMutation()
    const handleProviderDelete = () => {
        providerKeyMutation.mutate(props.providerKey.id)
    }
    return (
        <div class=" flex justify-between bg-gray-600 mx-2 p-3">
            <div class="flex gap-3 ">
                <p>{props.providerKey.provider}</p>
                <p>{props.providerKey.key}</p>
            </div>
			<Button onclick={handleProviderDelete}>Delete key</Button>
        </div>
    );
};
  
export default ProviderKeyCard;