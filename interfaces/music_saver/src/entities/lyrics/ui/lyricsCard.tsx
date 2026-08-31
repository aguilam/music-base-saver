import { Show } from "solid-js"
import { ShortLyrics} from "../model/types"
import { formatTime } from "~/shared/lib/utils"

interface LyricsCardProps {
    lyrics: ShortLyrics
}

const LyricsCard = (props: LyricsCardProps) => {
    return (
        <div class=" bg-gray-200 px-2 py-1 h-64 w-48">
            <div class="bg-gray-400 w-full h-3/4 mb-2 text-black text-sm overflow-hidden whitespace-pre-line">
                <Show when={props.lyrics.isSynced} fallback={
                    <p>{props.lyrics.plainText}</p>
                }>
                    <p>{props.lyrics.syncedText?.map((line) => formatTime(line.time / 1000) + ": " + line.text + "\n").join("\n")}</p>
                </Show>
            </div>
            <div class=" h-fit">
                <p>Lang: {props.lyrics.language}</p>
                <p>Offset: {props.lyrics.offset}</p>
            </div>
        </div>
    )
}

export default LyricsCard