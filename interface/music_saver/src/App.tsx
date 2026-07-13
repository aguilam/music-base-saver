import type { Component } from 'solid-js';
import { SidebarProvider, SidebarTrigger,  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarHeader } from "~/components/ui/sidebar"
const App: Component = () => {
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
        <p>Test</p>
      </main>
    </SidebarProvider>
  );
};

export default App;
