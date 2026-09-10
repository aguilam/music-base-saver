import { useNavigate } from "@solidjs/router";
import { createSignal, Component } from "solid-js";
import { Button } from "~/components/ui/button";
import { TextField, TextFieldLabel, TextFieldInput } from "~/components/ui/text-field";
import { createLoginMutation, createRegisterMutation, getMe } from "~/features/auth";
import { setUser } from "~/shared/store/user";

const AuthPage: Component = () => {
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = createSignal(true);
  const [username, setUsername] = createSignal("");
  const [password, setPassword] = createSignal("");
  const loginMutation = createLoginMutation()
  const registerMutation = createRegisterMutation()
  const handleSubmit = async (e: SubmitEvent) => {
    e.preventDefault();
    if (isLogin()) {
      loginMutation.mutate({username: username(), password: password()});
    } else {
      registerMutation.mutate({username: username(), password: password()});
    }
    const me = await getMe();
    setUser(me)
    navigate("/", { replace: true });
  };
  const toggleMode = () => {
    setIsLogin((prev) => !prev);
    setUsername("");
    setPassword("");
  };
  return (
    <div class="flex flex-col gap-2.5 p-8 items-center">
      <form onSubmit={handleSubmit} class="flex flex-col gap-2.5 w-full max-w-sm">
        <p class="text-xl font-bold text-center">{isLogin() ? "Sign in" : "Sign up"}</p>
        <TextField>
          <TextFieldLabel>Username</TextFieldLabel>
          <TextFieldInput value={username()} onInput={(e) => setUsername(e.currentTarget.value)} />
        </TextField>
        <TextField>
          <TextFieldLabel>Password</TextFieldLabel>
          <TextFieldInput
            type="password"
            value={password()}
            onInput={(e) => setPassword(e.currentTarget.value)}
          />
        </TextField>
        <Button type="submit">Continue</Button>
        <button
          type="button"
          onClick={toggleMode}
          class="text-sm text-blue-500 hover:underline mt-2"
        >
          {isLogin() ? "Registrate" : "Login"}
        </button>
      </form>
    </div>
  );
};
export default AuthPage;
