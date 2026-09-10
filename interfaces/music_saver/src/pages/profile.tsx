import { useParams } from "@solidjs/router";
import { Component, createEffect, createResource, createSignal, For, Show } from "solid-js";
import { Button } from "~/components/ui/button";

import { createUserPlaylistsQuery } from "~/entities/playlist/api/queries";
import PlaylistCard from "~/entities/playlist/ui/playlistCard";
import { createUserQuery, pathUsersMutation } from "~/entities/user";
import UserCredentialsDialog from "~/entities/user/ui/userCredentialsDialog";
import { createLogoutMutation } from "~/features/auth";
import { setUser, user } from "~/shared/store/user";

const ProfilePage: Component = () => {
  const params = useParams();
  const userQuery = createUserQuery(() => Number(params.id!));
  const userData = () => userQuery.data
  const userPlaylistsQuery = createUserPlaylistsQuery(() => userData()?.id!);
  const userPlaylists = () => userPlaylistsQuery.data;
  const [username, setUsername] = createSignal("");
  const [password, setPassword] = createSignal("");
  const [newPassword, setNewPassword] = createSignal("");
  const pathUser = pathUsersMutation();
  const logoutMutation = createLogoutMutation()
  const handleSaveUser = () => {
    if (password() !== newPassword()) {
      return;
    }
    if (userData()) {
      pathUser.mutate({ userId: userData()?.id!, username: username(), password: password() });
    }
  };

  createEffect(() => {
    const currentUserUsername = userData()?.username;
    if (currentUserUsername) {
      setUsername(currentUserUsername);
    }
  });
  const handleLogout = () => {
    logoutMutation.mutate()
    setUser({
      id: NaN,
      username: "",
      isAdmin: false,
    })
  }
  return (
    <div class=" h-screen w-full">
      <Show when={user.id === userData()?.id}>
        <Button class="absolute right-7" onClick={handleLogout}>Logout</Button>
      </Show>
      <div class="border-b-2 border-b-gray-300 w-full h-32 flex p-6 gap-4 items-center">
        <div class="w-16 h-16 bg-gray-600 flex items-center justify-center  rounded-full">
          <p class="text-4xl text-gray-400 font-bold uppercase ">{userData()?.username[0]}</p>
        </div>
        <p class="text-7xl font-extrabold text-gray-800">{userData()?.username}</p>
        <Show when={user.id === userData()?.id || user.isAdmin}>
          <UserCredentialsDialog
            buttonText="..."
            handleSave={handleSaveUser}
            username={username}
            setUsername={setUsername}
            password={password}
            setPassword={setPassword}
            repeatedPassword={newPassword}
            setRepeatedPassword={setNewPassword}
          />
        </Show>
      </div>
      <div class="w-full h-full px-4">
        <div class=" flex gap-3 overflow-x-auto">
          <For each={userPlaylists()}>{(playlist) => <PlaylistCard content={playlist} />}</For>
        </div>
      </div>
    </div>
  );
};
export default ProfilePage;
