import { Component, createSignal, For } from "solid-js";
import { addUserMutation, createUsersQuery } from "~/entities/user";
import { UserCard } from "~/entities/user/ui/userCard";
import UserCredentialsDialog from "~/entities/user/ui/userCredentialsDialog";

const UsersPage: Component = () => {
  const usersQuery = createUsersQuery();
  const users = () => usersQuery.data;
  const [username, setUsername] = createSignal("");
  const [password, setPassword] = createSignal("");
  const [repeatedPassword, setRepeatedPassword] = createSignal("");
  const addUser = addUserMutation();
  const handleAddUser = () => {
    if (password() !== repeatedPassword()) {
      return;
    }
    addUser.mutate({ username: username(), password: password() });
  };
  return (
    <div>
      <div class=" flex justify-between items-center m-3">
        <p>{users()?.length} Users</p>
        <UserCredentialsDialog
          buttonText="+"
          handleSave={handleAddUser}
          username={username}
          setUsername={setUsername}
          password={password}
          setPassword={setPassword}
          repeatedPassword={repeatedPassword}
          setRepeatedPassword={setRepeatedPassword}
        />
      </div>
      <For each={users()}>{(user) => <UserCard user={user} />}</For>
    </div>
  );
};
export default UsersPage;
