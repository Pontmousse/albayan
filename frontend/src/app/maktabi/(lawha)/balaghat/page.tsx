import { redirect } from "next/navigation";

type LegacyBalaghatPageProps = {
  searchParams: Promise<{ issue?: string | string[] }>;
};

export default async function LegacyBalaghatPage({
  searchParams,
}: LegacyBalaghatPageProps) {
  const { issue } = await searchParams;
  const issueId = Array.isArray(issue) ? issue[0] : issue;

  redirect(
    issueId ? `/balaghat?issue=${encodeURIComponent(issueId)}` : "/balaghat",
  );
}
