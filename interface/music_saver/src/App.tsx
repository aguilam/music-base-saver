import type { ParentComponent } from 'solid-js';
import { SidebarProvider, SidebarTrigger,  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarHeader } from "~/components/ui/sidebar"
const App: ParentComponent = (props) => {
  return (
    <SidebarProvider>
          <Sidebar>
      <SidebarHeader />
      <SidebarContent>
        <SidebarGroup />
        <SidebarGroup />
      </SidebarContent>
      <SidebarFooter />
    </Sidebar>
      <main>
        <SidebarTrigger />
        {props.children}
      </main>
    </SidebarProvider>
  );
};

export default App;
