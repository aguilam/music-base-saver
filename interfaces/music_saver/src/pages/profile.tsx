import { useParams } from "@solidjs/router";
import { Component, createEffect, createResource, createSignal, For, Show } from "solid-js";

import { createUserPlaylistsQuery } from "~/entities/playlist/api/queries";
import PlaylistCard from "~/entities/playlist/ui/playlistCard";
import { pathUsersMutation } from "~/entities/user";
import UserCredentialsDialog from "~/entities/user/ui/userCredentialsDialog";
import { getUser } from "~/shared/api/users";
import { user } from "~/shared/store/user";

const ProfilePage: Component = () => {
  const params = useParams();
  const [currentUser] = createResource(() => params.id!, getUser);
  const userPlaylistsQuery = createUserPlaylistsQuery(() => currentUser()?.id!);
  const userPlaylists = () => userPlaylistsQuery.data;
  const [username, setUsername] = createSignal("");
  const [password, setPassword] = createSignal("");
  const [newPassword, setNewPassword] = createSignal("");
  const pathUser = pathUsersMutation();

  const handleSaveUser = () => {
    if (password() !== newPassword()) {
      return;
    }
    if (currentUser()) {
      pathUser.mutate({ userId: currentUser()?.id!, username: username(), password: password() });
    }
  };

  createEffect(() => {
    const currentUserUsername = currentUser()?.username;
    if (currentUserUsername) {
      setUsername(currentUserUsername);
    }
  });

  return (
    <div class=" h-screen w-full">
      <div class="border-b-2 border-b-gray-300 w-full h-32 flex p-6 gap-4 items-center">
        <div class="w-16 h-16 bg-gray-600 flex items-center justify-center  rounded-full">
          <p class="text-4xl text-gray-400 font-bold uppercase ">{currentUser()?.username[0]}</p>
        </div>
        <p class="text-7xl font-extrabold text-gray-800">{currentUser()?.username}</p>
        <Show when={user.id === currentUser()?.id || user.role == "admin"}>
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
