import { Button } from "~/components/ui/button";
import { TextField, TextFieldLabel, TextFieldTextArea } from "~/components/ui/text-field";
import { createConfigQuery, changeConfigMutation } from "../api/queries";
import { createSignal, createEffect } from "solid-js";
import { user } from "~/shared/store/user";

const ConfigInput = () => {
	const [config, setConfig] = createSignal("")
	const configQuery = createConfigQuery()
	const changeConfig = changeConfigMutation()
	createEffect(() => {
		const data = configQuery.data
		if (data) {
			setConfig(data)
		}
	})
	const handleSaveConfig = () => {
		changeConfig.mutate(config())
	}
	return (
		<div>
			<TextField>
				<TextFieldLabel>Server Config</TextFieldLabel>
				<TextFieldTextArea class=" resize-none" rows={15} value={config()} onChange={(e) => setConfig(e.target.value)}/>
			</TextField>
			<Button onClick={handleSaveConfig} class=" mt-4 ml-4">Save</Button>
    	</div>
	);
};

export default ConfigInput;