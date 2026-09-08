import { Dialog, DialogContent, DialogPortal, DialogTrigger } from "~/shared/ui/dialog/dialog";
import { Button } from "~/components/ui/button";
import { TextField, TextFieldInput, TextFieldLabel } from "~/components/ui/text-field";
import { Accessor, createSignal, Setter } from "solid-js";
interface DialogProps {
  buttonText: string;
  handleSave: () => void;
  username: Accessor<string>;
  setUsername: Setter<string>;
  password: Accessor<string>;
  setPassword: Setter<string>;
  repeatedPassword: Accessor<string>;
  setRepeatedPassword: Setter<string>;
}
const UserCredentialsDialog = (props: DialogProps) => {
  const [isOpen, setIsOpen] = createSignal(false);

  const handleFormSave = () => {
    props.handleSave();
    setIsOpen(false);
  };
  return (
    <Dialog open={isOpen()} onOpenChange={(v) => setIsOpen(v)}>
      <DialogTrigger<typeof Button>
        as={(buttonProps) => <Button {...buttonProps}>{props.buttonText}</Button>}
      />
      <DialogPortal>
        <DialogContent class=" flex flex-col gap-2">
          <TextField value={props.username()} onChange={(v) => props.setUsername(v)}>
            <TextFieldLabel>Username</TextFieldLabel>
            <TextFieldInput />
          </TextField>
          <TextField value={props.password()} onChange={(v) => props.setPassword(v)}>
            <TextFieldLabel>Write new password</TextFieldLabel>
            <TextFieldInput />
          </TextField>
          <TextField
            value={props.repeatedPassword()}
            onChange={(v) => props.setRepeatedPassword(v)}
          >
            <TextFieldLabel>Repeat new password</TextFieldLabel>
            <TextFieldInput />
          </TextField>
          <Button onClick={handleFormSave}>Save</Button>
        </DialogContent>
      </DialogPortal>
    </Dialog>
  );
};

export default UserCredentialsDialog;
