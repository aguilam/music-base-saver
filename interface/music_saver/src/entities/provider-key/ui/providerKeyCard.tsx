import { createSignal, Show } from "solid-js";
import { ProviderKey } from "../model/types";
import NewProviderKeyForm from "./newProviderKeyForm";
import ProviderKeyInfo from "./providerKeyInfo";

interface ProviderKeyCardProps {
    providerKey: ProviderKey;
}

const ProviderKeyCard = (props: ProviderKeyCardProps) => {
    const [isChange, setIsChange] = createSignal(false)
    return (
        <Show when={isChange} fallback={
            <ProviderKeyInfo setIsChange={setIsChange} providerKey={props.providerKey} />
        }>
            <NewProviderKeyForm setIsChange={setIsChange} keyId={props.providerKey.id} />
        </Show>
    );
};
  
export default ProviderKeyCard;