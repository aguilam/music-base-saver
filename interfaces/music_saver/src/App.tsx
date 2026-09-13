import { QueryClient, QueryClientProvider } from "@tanstack/solid-query";
import { type ParentComponent } from "solid-js";
import AppSidebar from "./widgets/sidebar/sidebar";
const App: ParentComponent = (props) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 1000 * 60 * 5,
        refetchOnWindowFocus: false,
      },
    },
  });
  
  return (
    <QueryClientProvider client={queryClient}>
      <AppSidebar>
        {props.children}
      </AppSidebar>
    </QueryClientProvider>
  );
};

export default App;
