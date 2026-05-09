import { SessionDashboard } from "@/components/SessionDashboard";

export default function SessionPage({ params }: { params: { id: string } }) {
  return <SessionDashboard sessionId={params.id} />;
}
