import { useSearchParams } from "@solidjs/router";
import { Component, createSignal } from "solid-js";
import { TextField, TextFieldInput } from "~/components/ui/text-field";
import AlbumCard from "~/entities/album/ui/albumCard";
import ArtistCard from "~/entities/artists/ui/artistCard";
import TrackCard from "~/entities/track/ui/trackCard";
import { createExternalSearchQuery, createLibrarySearchQuery } from "~/features/search/api/queries";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "~/shared/ui/select";

type SearchOption = {
  value: string;
  label: string;
};

const SearchOptions: SearchOption[] = [
  { value: "local", label: "Local" },
  { value: "global", label: "Global" },
];

const SearchPage: Component = () => {
  const [selectedMode, setSelectedMode] = createSignal<SearchOption>();
  const [searchParams, setSearchParams] = useSearchParams();
  const query = () => searchParams.query?.toString() ?? "";
  const globalSearch = createExternalSearchQuery(query);
  const localSearched = createLibrarySearchQuery(query);
  const searchResults = () => {
    return searchParams.type?.toString() === "local"
      ? {
          tracks: localSearched.data?.pages.flatMap((page) => page.tracks) ?? [],
          albums: localSearched.data?.pages.flatMap((page) => page.albums) ?? [],
          artists: localSearched.data?.pages.flatMap((page) => page.artists) ?? [],
        }
      : {
          tracks: globalSearch.data?.pages.flatMap((page) => page.tracks) ?? [],
          albums: globalSearch.data?.pages.flatMap((page) => page.albums) ?? [],
          artists: globalSearch.data?.pages.flatMap((page) => page.artists) ?? [],
        };
  };
  const setSearchMode = (option: SearchOption) => {
    setSelectedMode(option);
    setSearchParams({ ...searchParams, type: option.value });
  };
  return (
    <div class=" px-2">
      <div class=" flex">
        <TextField>
          <TextFieldInput
            placeholder="Search query"
            value={searchParams.query?.toString()}
            onChange={(v) => setSearchParams({ ...searchParams, query: v.target.value })}
          />
        </TextField>
        <Select<SearchOption>
          options={SearchOptions}
          value={selectedMode()}
          optionValue="value"
          optionTextValue="label"
          itemComponent={(props) => (
            <SelectItem item={props.item}>{props.item.rawValue.label}</SelectItem>
          )}
          defaultValue={SearchOptions.find((state) => state.value == searchParams.type?.toString())}
          placeholder="Search Type"
          onChange={(newVal) => setSearchMode(newVal!)}
        >
          <SelectTrigger>
            <SelectValue<SearchOption>>{(state) => state.selectedOption()?.label}</SelectValue>
          </SelectTrigger>
          <SelectContent />
        </Select>
      </div>
      <div class=" pt-3 flex flex-col gap-2">
        <div class="grid grid-cols-3 gap-2 grid-rows-2 overflow-hidden">
          {searchResults()
            ?.tracks.slice(0, 8)
            .map((track) => (
              <TrackCard content={track} />
            ))}
        </div>
        <div class="flex gap-2">
          {searchResults()
            ?.albums.slice(0, 6)
            .map((album) => (
              <AlbumCard content={album} />
            ))}
        </div>
        <div class="flex gap-2">
          {searchResults()
            ?.artists.slice(0, 6)
            .map((artist) => (
              <ArtistCard content={artist} />
            ))}
        </div>
      </div>
    </div>
  );
};
export default SearchPage;
