import { Navigate, useNavigate } from '@solidjs/router';
import { Show, type ParentComponent } from 'solid-js';
import { SidebarProvider, SidebarTrigger,  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarHeader, SidebarGroupContent,SidebarMenu,SidebarMenuItem,SidebarMenuButton } from "~/components/ui/sidebar"
import { user } from './shared/store/user';
const App: ParentComponent = (props) => {
  const navigate = useNavigate();
  return (
    <Show when={user.id != ""} fallback={<Navigate href="/auth" />}>
      <SidebarProvider>
        <Sidebar>
          <SidebarHeader />
          <SidebarContent>
            <SidebarGroup >
              <SidebarGroupContent>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton onClick={() => navigate("/search")}>Search</SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton onClick={() => navigate("/")}>Main</SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton onClick={() => navigate("/statuses")}>Statuses</SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton onClick={() => navigate("/users")}>Users</SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup >
          </SidebarContent>
          <SidebarFooter >
            <SidebarGroupContent>
              <SidebarMenu>
                <SidebarMenuItem>
                    <SidebarMenuButton onClick={() => navigate("/settings")}>Settings</SidebarMenuButton>
                </SidebarMenuItem>
                <SidebarMenuItem>
                  <SidebarMenuButton onClick={() => navigate("/profile/")}>Profile</SidebarMenuButton>
                </SidebarMenuItem>
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarFooter>
        </Sidebar>
        <main>
          <SidebarTrigger />
          {props.children}
        </main>
      </SidebarProvider>
    </Show>
  );
};

export default App;
