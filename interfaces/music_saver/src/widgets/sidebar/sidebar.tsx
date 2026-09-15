import { Navigate, useNavigate } from "@solidjs/router";
import { Show, type ParentComponent } from "solid-js";
import {
  SidebarProvider,
  SidebarTrigger,
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarHeader,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarMenuSubItem,
  SidebarMenuSubButton,
} from "~/shared/ui/sidebar/sidebar";
import { user } from "~/shared/store/user";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "~/shared/ui/collapsible/collapsible";

const AppSidebar: ParentComponent = (props) => {
  const navigate = useNavigate();

  return (
    <SidebarProvider>
      <Show when={user.username} fallback={<Navigate href="/auth" />}>
        <Sidebar>
          <SidebarHeader />
          <SidebarContent>
            <SidebarGroup>
              <SidebarGroupContent>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton onClick={() => navigate("/search?type=local")}>
                      Search
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <Collapsible>
                      <SidebarMenuButton>
                        <CollapsibleTrigger>Content</CollapsibleTrigger>
                      </SidebarMenuButton>
                      <CollapsibleContent>
                        <SidebarMenuSubItem>
                          <SidebarMenuSubButton onClick={() => navigate("/artists")}>
                            Artists
                          </SidebarMenuSubButton>
                        </SidebarMenuSubItem>
                        <SidebarMenuSubItem>
                          <SidebarMenuSubButton onClick={() => navigate("/playlists")}>
                            Playlists
                          </SidebarMenuSubButton>
                        </SidebarMenuSubItem>
                        <SidebarMenuSubItem>
                          <SidebarMenuSubButton onClick={() => navigate("/albums")}>
                            Albums
                          </SidebarMenuSubButton>
                        </SidebarMenuSubItem>
                        <SidebarMenuSubItem>
                          <SidebarMenuSubButton onClick={() => navigate("/tracks")}>
                            Tracks
                          </SidebarMenuSubButton>
                        </SidebarMenuSubItem>
                      </CollapsibleContent>
                    </Collapsible>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton onClick={() => navigate("/")}>Main</SidebarMenuButton>
                  </SidebarMenuItem>
                  <Show when={user.isAdmin}>
                    <SidebarMenuItem>
                      <SidebarMenuButton onClick={() => navigate("/statuses")}>
                        Statuses
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                    <SidebarMenuItem>
                      <SidebarMenuButton onClick={() => navigate("/users")}>
                        Users
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  </Show>
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </SidebarContent>
          <SidebarFooter>
            <SidebarGroupContent>
              <SidebarMenu>
                <SidebarMenuItem>
                  <SidebarMenuButton onClick={() => navigate("/settings")}>
                    Settings
                  </SidebarMenuButton>
                </SidebarMenuItem>
                <SidebarMenuItem>
                  <SidebarMenuButton onClick={() => navigate(`/profile/${user.id}`)}>
                    Profile
                  </SidebarMenuButton>
                </SidebarMenuItem>
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarFooter>
        </Sidebar>
      </Show>
      <main class="w-full h-full">
        <Show when={user.username}>
          <SidebarTrigger />
        </Show>
        {props.children}
      </main>
    </SidebarProvider>
  );
};
export default AppSidebar;
