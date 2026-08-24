import { auth } from "@clerk/nextjs/server";
import { fetchPublicJournal } from "@/lib/api/public";
import { EarlyStageHome } from "@/components/journal/early-stage-home";
import { PublishedJournalHome } from "@/components/journal/published-journal-home";
import { QuranicOpening } from "@/components/journal/quranic-opening";

/**
 * الرئيسية العامة — تنتقل تلقائيًا بين واجهتين (لا يظهر هذا للزوّار):
 * - published_count = 0 → EarlyStageHome (مرحلة إعداد أولى الإصدارات)
 * - published_count > 0 → PublishedJournalHome (قائمة من API)
 *
 * مصدر الحقيقة: GET /api/v1/public/journal — لا تُضف مقالات ثابتة هنا.
 */
export default async function Home() {
  const journal = await fetchPublicJournal();
  const { isAuthenticated, userId } = await auth();
  const signedIn = Boolean(isAuthenticated || userId);

  return (
    <div className="flex flex-1 flex-col">
      <main className="flex-1">
        <QuranicOpening />
        {journal.published_count === 0 ? (
          <EarlyStageHome signedIn={signedIn} />
        ) : (
          <PublishedJournalHome
            articles={journal.articles}
            signedIn={signedIn}
          />
        )}
      </main>
    </div>
  );
}
