import { formatTime } from "~/shared/lib/utils"
import { ShortMusicVideo } from "../model/types"

interface MusicVideoCardProps {
    musicVideo: ShortMusicVideo
}

const MusicVideoCard = (props: MusicVideoCardProps) => {
    return (
        <div class=" w-64 h-32 relative">
            <div class=" w-full h-full bg-amber-50"/>
            <div class=" absolute right-2 bottom-2 bg-black w-fit px-2">
                <p class=" text-white text-sm">{formatTime(props.musicVideo.duration ?? 0)}</p>
            </div>
        </div>
    )
}

export default MusicVideoCard