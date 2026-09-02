import { Button } from "~/components/ui/button"
import { TextField, TextFieldInput } from "~/components/ui/text-field"
import { changeProviderKeyMutation, createProviderKeyMutation } from "../api/queries"
import { createSignal, Setter } from "solid-js"
interface NewProviderKeyProps {
    keyId?: number
    setIsChange: Setter<boolean>
}
const NewProviderKeyForm = (props: NewProviderKeyProps) => {
    const createKeyMutation = createProviderKeyMutation()
    const changeKeyMutation = changeProviderKeyMutation()
    const [provider, setProvider] = createSignal("")
    const [key, setKey] = createSignal("")
    const handleProviderKeySave = () => {
        if (props.keyId) {
            changeKeyMutation.mutate({id: props.keyId, provider: provider(), key: key()})
            props.setIsChange(false)
        } else {
            createKeyMutation.mutate({provider: provider(), key: key()})
            props.setIsChange(false)
        }
    } 
    return (
        <div class=" flex justify-between bg-gray-600 mx-2 p-3">
            <div class="flex gap-3">
                <TextField>
                    <TextFieldInput placeholder="provider" value={provider()} onchange={(e) => setProvider(e.currentTarget.value)} />
                </TextField>
                <TextField>
                    <TextFieldInput placeholder="key" value={key()} onchange={(e) => setKey(e.currentTarget.value)}></TextFieldInput>
                </TextField>
            </div>
			<Button onclick={handleProviderKeySave}>Save</Button>
        </div>
    )
}

export default NewProviderKeyForm