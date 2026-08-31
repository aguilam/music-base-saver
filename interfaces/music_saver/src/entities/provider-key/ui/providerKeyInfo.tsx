import { Setter } from "solid-js";
import { deleteProviderKeyMutation } from "../api/queries";
import { ProviderKey } from "../model/types";
import { Button } from "~/components/ui/button";

interface ProviderKeyInfoProps {
    providerKey: ProviderKey;
    setIsChange: Setter<boolean>
}

const ProviderKeyInfo = (props: ProviderKeyInfoProps) => {
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
            <div class=" flex gap-2">
                <Button onclick={() => props.setIsChange(true)}>Change</Button>
                <Button onclick={handleProviderDelete}>Delete key</Button>
            </div>
        </div>
    );
};
  
export default ProviderKeyInfo;