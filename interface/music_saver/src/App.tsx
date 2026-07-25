import { useNavigate } from '@solidjs/router';
import type { ParentComponent } from 'solid-js';
import { SidebarProvider, SidebarTrigger,  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarHeader, SidebarGroupContent,SidebarMenu,SidebarMenuItem,SidebarMenuButton } from "~/components/ui/sidebar"
const App: ParentComponent = (props) => {
  const navigate = useNavigate();
  return (
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
  );
};

export default App;
