import { useParams } from "@solidjs/router"
import { Component, For, Show } from "solid-js"
import ArtistsNames from "~/entities/artists/ui/artistsNames"
import LyricsCard from "~/entities/lyrics/ui/lyricsCard"
import MusicVideoCard from "~/entities/music-video/ui/musicVideoCard"
import { createTrackQuery } from "~/entities/track"
import { formatTimeToString } from "~/shared/lib/utils"
import Cover from "~/shared/ui/cover"

const TrackPage: Component = () => {
    const params = useParams()
    const trackQuery = createTrackQuery(() => Number(params.id));

    return (
        <Show when={trackQuery.data} fallback={trackQuery.isLoading ? <div>Loading</div> : <div>Not found</div>}>
            {(track) => (
                <div>
                    <div class="flex gap-5">
                        <Cover coverUri={track().coverUri} type="track" size="lg"/>
                        <div class="flex flex-col justify-between h-full py-5">
                            <div>
                                <p class=" text-slate-400">Track</p>
                                <p class=" text-5xl font-bold">{track().title}</p>
                                <div class="flex gap-1 text-secondary-text">
                                  <ArtistsNames artists={track().artists}/>
                                  <p>{track().year}</p>
                                  <p>{formatTimeToString(track().duration ?? 0)}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div>
                        <p>Lyrics</p>
                        <div class=" flex gap-3">
                            <For each={track().lyrics}>
                                {(lyrics) => <LyricsCard lyrics={lyrics}/>}
                            </For>
                        </div>
                    </div>
                    <div>
                        <p>Music Videos</p>
                        <div class=" flex gap-3">
                            <For each={track().musicVideos}>
                                {(musicVideo) => <MusicVideoCard musicVideo={musicVideo}/>}
                            </For>
                        </div>
                    </div>
                </div>
            )}
        </Show>
    )
}
export default TrackPage