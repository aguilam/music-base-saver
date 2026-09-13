import {
    createTable,
    tableFeatures,
    columnSizingFeature,
    columnResizingFeature,
    columnVisibilityFeature,
    createColumnHelper,
    FlexRender,
  } from '@tanstack/solid-table'
import { ShortTrack } from '../model/types'
import { For, Show } from 'solid-js'
import { Button } from '~/components/ui/button'
import { Popover, PopoverContent,PopoverPortal,PopoverTrigger } from '~/shared/ui/popover/popover'
import { formatTime } from '~/shared/lib/utils'
import { Checkbox, CheckboxControl, CheckboxInput, CheckboxLabel } from '~/shared/ui/checkbox/checkbox'
import { A } from '@solidjs/router'
const features = tableFeatures({
    columnSizingFeature,
    columnResizingFeature,
    columnVisibilityFeature
})
const columnHelper = createColumnHelper<typeof features, ShortTrack>()

const columns = columnHelper.columns([
    columnHelper.accessor("id",{
        header: "#",
        cell: (info) => info.getValue()
    }),
    columnHelper.accessor("title",{
        header: "title",
        cell: (info) => <A href={`/tracks/${info.row.original.id}`}>{info.getValue()}</A>
    }),
    columnHelper.accessor("createdAt",{
        header: "Adding date",
        cell: (info) => new Date(info.getValue()).toLocaleDateString()
    }),
    columnHelper.accessor("year",{
        header: "Year",
        cell: (info) => info.getValue()
    }),
    columnHelper.accessor("duration",{
        header: "Duration",
        cell: (info) => formatTime(info.getValue())
    }),
    columnHelper.accessor("trackGain",{
        header: "Track Gain",
        cell: (info) => info.getValue()
    }),
    columnHelper.accessor("trackPeak",{
        header: "Track Peak",
        cell: (info) => info.getValue()
    }),
])

interface TrackListProps {
    tracks: ShortTrack[]
}

const TrackList = (props: TrackListProps) => {
    const table = createTable({
        features,
        columns,
        get data() {
            return props.tracks
        },
        columnResizeMode: "onChange"
    })

    return (
        <table class='w-full'>
          <thead class=' border-b border-b-gray-400'>
            <tr class=' group'>
                <For each={table.getHeaderGroups()}>
                  {(headerGroup) => (
                      <For each={headerGroup.headers}>
                        {(header) => (
                          <th class=' text-start relative' colSpan={header.colSpan} style={{ width: `${header.getSize()}px` }}>
                            <Show when={!header.isPlaceholder}>
                              <FlexRender header={header} />
                            </Show>
                            <div
                                onDblClick={() => header.column.resetSize()}
                                onMouseDown={header.getResizeHandler()}
                                onTouchStart={header.getResizeHandler()}
                                class={` opacity-0 group-hover:opacity-100 hover:opacity-100 absolute top-0 right-0 h-full w-2 cursor-col-resize select-none touch-none bg-gray-500 ${header.column.getIsResizing() ? ' opacity-100' : ''}`}
                            />
                          </th>
                        )}
                      </For>
                  )}
                </For>
                <th class="opacity-0 group-hover:opacity-100 hover:opacity-100">
                    <Popover>
                        <PopoverTrigger<typeof Button>
                            as={(props) => (
                                <Button class='w-fit h-fit p-0' variant="ghost" {...props}>-</Button>
            			    )} 
                        />
                        <PopoverPortal>
                            <PopoverContent class=' w-40'>
                                <For each={table.getAllLeafColumns()}>
                                  {(column) => (
                                    <div>
                                        <Checkbox class='flex gap-2' checked={column.getIsVisible()} onChange={(v) => column.toggleVisibility(v)}>
                                            <CheckboxInput />
                                            <CheckboxControl />
                                            <CheckboxLabel>{column.columnDef.header?.toString()}</CheckboxLabel>
                                        </Checkbox>
                                    </div>
                                  )}
                                </For>
                            </PopoverContent>
                        </PopoverPortal>
                    </Popover>
                </th>
            </tr>
          </thead>
          <tbody>
            <For each={table.getRowModel().rows}>
              {(row) => (
                <tr>
                  <For each={row.getVisibleCells()}>
                    {(cell) => (
                      <td style={{ width: `${cell.column.getSize()}px` }}>
                        <FlexRender cell={cell} />
                      </td>
                    )}
                  </For>
                </tr>
              )}
            </For>
          </tbody>
          <tfoot>
            <For each={table.getFooterGroups()}>
              {(footerGroup) => (
                <tr>
                  <For each={footerGroup.headers}>
                    {(header) => (
                      <th colSpan={header.colSpan}>
                        <Show when={!header.isPlaceholder}>
                          <FlexRender footer={header} />
                        </Show>
                      </th>
                    )}
                  </For>
                </tr>
              )}
            </For>
          </tfoot>
        </table>
    )
}

export default TrackList