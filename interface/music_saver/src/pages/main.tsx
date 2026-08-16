import { Component } from "solid-js"
import { createServerStatsQuery } from "~/entities/server"
const MainPage: Component = () => {
    const serverStatsQuery = createServerStatsQuery()
    const serverStats = () => serverStatsQuery.data
    return (
        <div class=" px-4 flex flex-col gap-4">
            <div class="flex gap-2">
                <div class=" bg-amber-50 rounded-2xl border border-b-gray-950 h-16 w-1/5 flex flex-col items-center py-2">
                    <p class=" text-gray-800">Total Artists</p>
                    <p class=" text-gray-600">{serverStats()?.artistsTotal}</p>
                </div>
                <div class=" bg-amber-50 rounded-2xl border border-b-gray-950 h-16 w-1/5 flex flex-col items-center py-2">
                    <p class=" text-gray-800">Artists with Covers</p>
                    <p class=" text-gray-600">{serverStats()?.artistsWithCover}</p>
                </div>
            </div>
            <div class="flex gap-2">
                <div class=" bg-amber-50 rounded-2xl border border-b-gray-950 h-16 w-1/5 flex flex-col items-center py-2">
                    <p class=" text-gray-800">Total albums</p>
                    <p class=" text-gray-600">{serverStats()?.albumsTotal}</p>
                </div>
                <div class=" bg-amber-50 rounded-2xl border border-b-gray-950 h-16 w-1/5 flex flex-col items-center py-2">
                    <p class=" text-gray-800">Albums with covers</p>
                    <p class=" text-gray-600">{serverStats()?.albumsWithCover}</p>
                </div>
            </div>
            <div class="flex gap-2">
                <div class=" bg-amber-50 rounded-2xl border border-b-gray-950 h-16 w-1/5 flex flex-col items-center py-2">
                    <p class=" text-gray-800">Total tracks</p>
                    <p class=" text-gray-600">{serverStats()?.tracksTotal}</p>
                </div>
                <div class=" bg-amber-50 rounded-2xl border border-b-gray-950 h-16 w-1/5 flex flex-col items-center py-2">
                    <p class=" text-gray-800">Tracks with lyrics</p>
                    <p class=" text-gray-600">{serverStats()?.tracksWithLyrics}</p>
                </div>
                <div class=" bg-amber-50 rounded-2xl border border-b-gray-950 h-16 w-1/5 flex flex-col items-center py-2">
                    <p class=" text-gray-800">Tracks with videos</p>
                    <p class=" text-gray-600">{serverStats()?.tracksWithVideos}</p>
                </div>
            </div>
            <div class="flex gap-2">
                <div class=" bg-amber-50 rounded-2xl border border-b-gray-950 h-16 w-1/5 flex flex-col items-center py-2">
                    <p class=" text-gray-800">Total genres</p>
                    <p class=" text-gray-600">{serverStats()?.genresTotal}</p>
                </div>
                <div class=" bg-amber-50 rounded-2xl border border-b-gray-950 h-16 w-1/5 flex flex-col items-center py-2">
                    <p class=" text-gray-800">Artists with genres</p>
                    <p class=" text-gray-600">{serverStats()?.artistsWithGenres}</p>
                </div>
                <div class=" bg-amber-50 rounded-2xl border border-b-gray-950 h-16 w-1/5 flex flex-col items-center py-2">
                    <p class=" text-gray-800">Albums with genres</p>
                    <p class=" text-gray-600">{serverStats()?.albumsWithGenres}</p>
                </div>
                <div class=" bg-amber-50 rounded-2xl border border-b-gray-950 h-16 w-1/5 flex flex-col items-center py-2">
                    <p class=" text-gray-800">Tracks with genres</p>
                    <p class=" text-gray-600">{serverStats()?.tracksWithGenres}</p>
                </div>
            </div>
            <div class="flex gap-2">
                <div class=" bg-amber-50 rounded-2xl border border-b-gray-950 h-16 w-1/5 flex flex-col items-center py-2">
                    <p class=" text-gray-800">Total moods</p>
                    <p class=" text-gray-600">{serverStats()?.moodsTotal}</p>
                </div>
                <div class=" bg-amber-50 rounded-2xl border border-b-gray-950 h-16 w-1/5 flex flex-col items-center py-2">
                    <p class=" text-gray-800">Tracks with moods</p>
                    <p class=" text-gray-600">{serverStats()?.tracksWithMoods}</p>
                </div>
            </div>
        </div>
    )
}
export default MainPage
