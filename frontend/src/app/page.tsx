import { fetchPublicJournal } from "@/lib/api/public";
import { EarlyStageHome } from "@/components/journal/early-stage-home";
import { PublishedJournalHome } from "@/components/journal/published-journal-home";
import { QuranicOpening } from "@/components/journal/quranic-opening";

/**
 * الرئيسية العامة — تنتقل تلقائيًا بين واجهتين:
 * - published_count = 0 → EarlyStageHome (مرحلة مبكرة، بلا بيانات مختلقة)
 * - published_count > 0 → PublishedJournalHome (قائمة من API)
 *
 * مصدر الحقيقة: GET /api/v1/public/journal — لا تُضف مقالات ثابتة هنا.
 */
export default async function Home() {
  const journal = await fetchPublicJournal();

  return (
    <div className="flex flex-1 flex-col">
      <main className="flex-1">
        <QuranicOpening />
        {journal.published_count === 0 ? (
          <EarlyStageHome />
        ) : (
          <PublishedJournalHome articles={journal.articles} />
        )}
      </main>
    </div>
  );
}
