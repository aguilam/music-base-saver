import { useNavigate, useParams } from "@solidjs/router";
import { createSignal, For, Show } from "solid-js";
import Cover from "~/shared/ui/cover";
import TrackCard from "~/entities/track/ui/trackCard";
import { changePlaylistMutation, createPlaylistQuery, deletePlaylistMutation } from "~/entities/playlist/api/queries";
import { formatTimeToString } from "~/shared/lib/utils";
import UserNames from "~/entities/user/ui/userNames";
import { Popover, PopoverContent, PopoverPortal, PopoverTrigger } from "~/shared/ui/popover/popover";
import { Button } from "~/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogPortal, DialogTitle, DialogTrigger } from "~/shared/ui/dialog/dialog";
import { TextField, TextFieldInput, TextFieldLabel } from "~/components/ui/text-field";
import { Switch, SwitchControl, SwitchInput, SwitchLabel, SwitchThumb } from "~/shared/ui/switch/switch";

const PlaylistPage = () => {
	const [title, setTitle] = createSignal("");
	const [open, setOpen] = createSignal(false);
	const [isPublic, setIsPublic] = createSignal(false);
  const params = useParams()
	const navigate = useNavigate()
  const playlistQuery = createPlaylistQuery(() => Number(params.id));
	const deletePlaylist = deletePlaylistMutation()
	const changePlaylist = changePlaylistMutation()
	const handleDeletePlaylist = () => {
		deletePlaylist.mutate(Number(params.id))
		navigate(-1)
	}
	const handleChangePlaylist = async (title: string | null, trackIds: number[] | null, ownerIds: number[] | null, isPublic: boolean | null) => {
		const changedPlaylist = await changePlaylist.mutate({id: Number(params.id), title: title, trackIds: trackIds, ownerIds: ownerIds, isPublic: isPublic})
		setOpen(false);
	}
  return (
    <Show when={playlistQuery.data} fallback={playlistQuery.isLoading ? <div>Loading</div> : <div>Not found</div>}>
      {(playlist) => (
        <div>
          <div class="h-48 flex gap-5">
            <Cover coverUri={playlist().coverUri} type="playlist" size="md" />
            <div class="flex flex-col justify-between h-full py-5">
              <div>
                <p class=" text-secondary-text">Playlist</p>
                <p class=" text-5xl font-bold text-primary-text">
                  {playlist().title}
                </p>
                <div class="flex gap-1 text-secondary-text">
                  <UserNames users={playlist().owners}/>
                  <p>{playlist().tracksCount} tracks</p>
                  <p>{formatTimeToString(playlist().duration ?? 0)}</p>
                  <Popover>
            			  <PopoverTrigger<typeof Button>
            			    as={(props) => (
            			      <Button variant="ghost" {...props}>. . .</Button>
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
															<div class=" flex flex-col gap-2">
																<TextField value={title()} onChange={(v) => setTitle(v)}>
																	<TextFieldLabel>Title</TextFieldLabel>
																	<TextFieldInput/>
																</TextField>
																<Switch class="flex items-center gap-x-2" checked={isPublic()} onChange={(v) => setIsPublic(v)}>
																	<SwitchLabel>Is Public</SwitchLabel>
    														  <SwitchInput />
    														  <SwitchControl>
    														    <SwitchThumb />
    														  </SwitchControl>
    														</Switch>
																<Button class=" self-end" onClick={() => handleChangePlaylist(title(),null,null,isPublic())}>Save</Button>
															</div>
    										    </DialogContent>
    										  </DialogPortal>
    										</Dialog>
            			      
												<Button variant="ghost" onclick={handleDeletePlaylist}>Delete</Button>
            			    </PopoverContent>
            			  </PopoverPortal>
            			</Popover>
                </div>
              </div>
            </div>
          </div>
          {playlist().tracks && (
            <div class="gap-5">
                <For each={playlist().tracks}>
                    {(track) => <TrackCard content={track} />}
                </For>
            </div>
          )}
        </div>
      )}
    </Show>
  );
};

export default PlaylistPage;