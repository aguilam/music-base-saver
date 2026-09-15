import { createInfiniteQuery } from "@tanstack/solid-query";
import { externalSearch, librarySearch } from "./endpoints";
import { Accessor } from "solid-js";

export function createLibrarySearchQuery(query: Accessor<string>) {
  return createInfiniteQuery(() => ({
    queryKey: ["search", "library", query()],
    queryFn: () => librarySearch(query(), 0),
    initialPageParam: 0,
    getNextPageParam: (lastPage, pages) => 0,
  }));
}

export function createExternalSearchQuery(query: Accessor<string>) {
  return createInfiniteQuery(() => ({
    queryKey: ["search", "external", query()],
    queryFn: () => externalSearch(query()),
    initialPageParam: 0,
    getNextPageParam: (lastPage, pages) => 0,
  }));
}
