import { useNavigate, useParams } from "@solidjs/router";
import { createEffect, createSignal, For, Show } from "solid-js";
import Cover from "~/shared/ui/cover";
import TrackCard from "~/entities/track/ui/trackCard";
import {
  changePlaylistMutation,
  createPlaylistQuery,
  deletePlaylistMutation,
} from "~/entities/playlist/api/queries";
import { formatTimeToString } from "~/shared/lib/utils";
import UserNames from "~/entities/user/ui/userNames";
import {
  Popover,
  PopoverContent,
  PopoverPortal,
  PopoverTrigger,
} from "~/shared/ui/popover/popover";
import { Button } from "~/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogPortal,
  DialogTitle,
  DialogTrigger,
} from "~/shared/ui/dialog/dialog";
import { TextField, TextFieldInput, TextFieldLabel } from "~/components/ui/text-field";
import {
  Switch,
  SwitchControl,
  SwitchInput,
  SwitchLabel,
  SwitchThumb,
} from "~/shared/ui/switch/switch";
import {
  Combobox,
  ComboboxContent,
  ComboboxControl,
  ComboboxInput,
  ComboboxItem,
  ComboboxItemLabel,
  ComboboxLabel,
  ComboboxPortal,
  ComboboxTrigger,
} from "~/shared/ui/combobox/combobox";
import { Badge } from "~/shared/ui/badge/badge";
import { createUsersQuery, ListedUser } from "~/entities/user";
import TrackList from "~/entities/track/ui/trackList";
import { ShortTrack } from "~/entities/track";
import {
  Search,
  SearchContent,
  SearchControl,
  SearchItem,
  SearchItemLabel,
  SearchListbox,
  SearchNoResult,
  SearchPortal,
} from "~/shared/ui/search/search";
import { createLibrarySearchQuery } from "~/features/search";

const PlaylistPage = () => {
  const [title, setTitle] = createSignal("");
  const [tracks, setTracks] = createSignal<number[]>([]);
  const [searchQuery, setSearchQuery] = createSignal("");
  const [searchedTrack, setSearchedTracks] = createSignal<ShortTrack[]>([]);
  const [playlistOwners, setPlaylistOwners] = createSignal<ListedUser[]>([]);
  const [open, setOpen] = createSignal(false);
  const [isPublic, setIsPublic] = createSignal(false);
  const params = useParams();
  const navigate = useNavigate();
  const playlistQuery = createPlaylistQuery(() => Number(params.id));
  const deletePlaylist = deletePlaylistMutation();
  const changePlaylist = changePlaylistMutation();
  const usersQuery = createUsersQuery();
  const users = () => usersQuery.data;
  const handleDeletePlaylist = () => {
    deletePlaylist.mutate(Number(params.id));
    navigate(-1);
  };
  const handleChangePlaylist = async (
    title: string | null,
    trackIds: number[] | null,
    ownerIds: number[] | null,
    isPublic: boolean | null,
  ) => {
    const changedPlaylist = await changePlaylist.mutate({
      id: Number(params.id),
      title: title,
      trackIds: trackIds,
      ownerIds: ownerIds,
      isPublic: isPublic,
    });
    setOpen(false);
  };
  const handleAddNewTrack = (newTrackId: number) => {
    if (tracks().some((track) => track == newTrackId)) return;
    setTracks((prev) => [...(prev ?? []), newTrackId]);
    handleChangePlaylist(null, tracks(), null, null);
  };
  createEffect(() => {
    const data = playlistQuery.data;

    if (data?.owners) {
      setPlaylistOwners(
        data.owners.map((owner) => ({
          id: owner.id,
          username: owner.username,
          isAdmin: false,
        })),
      );
    }
    if (data?.tracks) {
      setTracks(data.tracks.map((track) => track.id));
    }
    const librarySearch = createLibrarySearchQuery(searchQuery());
    setSearchedTracks(librarySearch.data?.pages.flatMap((result) => result.tracks) ?? []);
  });

  return (
    <Show
      when={playlistQuery.data}
      fallback={playlistQuery.isLoading ? <div>Loading</div> : <div>Not found</div>}
    >
      {(playlist) => (
        <div>
          <div class="h-48 flex gap-5">
            <Cover coverUri={playlist().coverUri} type="playlist" size="md" />
            <div class="flex flex-col justify-between h-full py-5">
              <div>
                <p class=" text-secondary-text">Playlist</p>
                <p class=" text-5xl font-bold text-primary-text">{playlist().title}</p>
                <div class="flex gap-1 text-secondary-text">
                  <UserNames users={playlist().owners} />
                  <p>{playlist().tracksCount} tracks</p>
                  <p>{formatTimeToString(playlist().duration ?? 0)}</p>
                  <Popover>
                    <PopoverTrigger<typeof Button>
                      as={(props) => (
                        <Button variant="ghost" {...props}>
                          . . .
                        </Button>
                      )}
                    />
                    <PopoverPortal>
                      <PopoverContent class="w-40 flex flex-col p-1">
                        <Dialog open={open()} onOpenChange={(v) => setOpen(v)}>
                          <DialogTrigger<typeof Button>
                            as={(props) => (
                              <Button variant="ghost" {...props}>
                                Change
                              </Button>
                            )}
                          />
                          <DialogPortal>
                            <DialogContent class="sm:max-w-[425px]">
                              <DialogHeader>
                                <DialogTitle>Change Playlist</DialogTitle>
                              </DialogHeader>
                              <div class=" w-2flex flex-col gap-2">
                                <TextField value={title()} onChange={(v) => setTitle(v)}>
                                  <TextFieldLabel>Title</TextFieldLabel>
                                  <TextFieldInput />
                                </TextField>
                                <Switch
                                  class="flex items-center gap-x-2"
                                  checked={isPublic()}
                                  onChange={(v) => setIsPublic(v)}
                                >
                                  <SwitchLabel>Is Public</SwitchLabel>
                                  <SwitchInput />
                                  <SwitchControl>
                                    <SwitchThumb />
                                  </SwitchControl>
                                </Switch>
                                <Combobox<ListedUser>
                                  multiple
                                  options={users() ?? []}
                                  onChange={setPlaylistOwners}
                                  defaultValue={playlistOwners()}
                                  optionValue={"id"}
                                  optionTextValue={"username"}
                                  itemComponent={(props) => (
                                    <ComboboxItem item={props.item}>
                                      <ComboboxItemLabel>
                                        {props.item.rawValue.username}
                                      </ComboboxItemLabel>
                                    </ComboboxItem>
                                  )}
                                >
                                  <ComboboxLabel>Playlist owners</ComboboxLabel>
                                  <ComboboxControl<ListedUser> class="h-fit min-h-9 w-full max-w-sm justify-between">
                                    {(state) => (
                                      <>
                                        <div class="flex flex-wrap items-center gap-1">
                                          <For each={state.selectedOptions()}>
                                            {(option) => (
                                              <Badge class="rounded-sm">
                                                {option.username}
                                                <button
                                                  type="button"
                                                  class="rounded-full"
                                                  onClick={() => {
                                                    state.remove(option);
                                                  }}
                                                >
                                                  <svg
                                                    xmlns="http://www.w3.org/2000/svg"
                                                    viewBox="0 0 24 24"
                                                    class="size-3"
                                                  >
                                                    <path
                                                      fill="none"
                                                      stroke="currentColor"
                                                      stroke-linecap="round"
                                                      stroke-linejoin="round"
                                                      stroke-width="2"
                                                      d="M18 6L6 18M6 6l12 12"
                                                    />
                                                  </svg>
                                                </button>
                                              </Badge>
                                            )}
                                          </For>
                                          <ComboboxInput />
                                        </div>
                                        <ComboboxTrigger />
                                      </>
                                    )}
                                  </ComboboxControl>
                                  <ComboboxPortal>
                                    <ComboboxContent />
                                  </ComboboxPortal>
                                </Combobox>
                                <Button
                                  onClick={() =>
                                    handleChangePlaylist(
                                      title(),
                                      null,
                                      playlistOwners().map((owner) => owner.id),
                                      isPublic(),
                                    )
                                  }
                                >
                                  Save
                                </Button>
                              </div>
                            </DialogContent>
                          </DialogPortal>
                        </Dialog>
                        <Button variant="ghost" onclick={handleDeletePlaylist}>
                          Delete
                        </Button>
                      </PopoverContent>
                    </PopoverPortal>
                  </Popover>
                </div>
              </div>
            </div>
            <div>
              <Search<ShortTrack>
                triggerMode="focus"
                debounceOptionsMillisecond={300}
                options={searchedTrack()}
                onInputChange={(query) => setSearchQuery(query)}
                optionValue={"id"}
                optionLabel={"title"}
                placeholder="Search tracks"
                itemComponent={(props) => (
                  <SearchItem
                    item={props.item}
                    onPointerDown={() => handleAddNewTrack(props.item.rawValue.id)}
                  >
                    <SearchItemLabel>{props.item.rawValue.title}</SearchItemLabel>
                  </SearchItem>
                )}
                class="w-full gap-0 "
              >
                <SearchControl
                  aria-label="Tracks Search"
                  class="w-full rounded-t-md rounded-b-none"
                />
                <SearchPortal>
                  <SearchContent>
                    <div class="bg-popover text-popover-foreground border-input min-h-40 rounded-b-md border border-t-0">
                      <SearchListbox />
                      <SearchNoResult>No tracks found</SearchNoResult>
                    </div>
                  </SearchContent>
                </SearchPortal>
              </Search>
            </div>
          </div>
          {playlist().tracks && <TrackList tracks={playlist().tracks} />}
        </div>
      )}
    </Show>
  );
};

export default PlaylistPage;
