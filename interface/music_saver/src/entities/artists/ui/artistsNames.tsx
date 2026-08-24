import { For } from "solid-js"
import { ShortArtist } from "../model/types"
import { A } from "@solidjs/router"

interface ArtistsNamesProps {
    artists: ShortArtist[]
}
const ArtistsNames = (props: ArtistsNamesProps) => {
    return (
        <div class=" flex gap-1 text-black">
            <For each={props.artists}>
                {(artist) => <A href={`/artist/${artist.id}`} class="text-black hover:text-gray-700">{artist.name}</A>}
            </For>
        </div>
    )
}

export default ArtistsNames