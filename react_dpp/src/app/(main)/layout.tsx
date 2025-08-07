import { Layout } from "@/components/layout/Layout";
import { SidebarProvider } from "@/components/layout/SidebarProvider";

interface MainLayoutProps {
  children: React.ReactNode;
}

export default function MainLayout({ children }: MainLayoutProps) {
  return (
    <SidebarProvider>
      <Layout>{children}</Layout>
    </SidebarProvider>
  );
} 