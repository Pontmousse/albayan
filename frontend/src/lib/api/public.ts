const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type PublicArticleAuthor = {
  full_name: string | null;
  author_order: number;
};

export type PublicArticleSummary = {
  id: string;
  title: string;
  abstract: string | null;
  published_at: string;
  authors: PublicArticleAuthor[];
};

export type PublicJournalResponse = {
  published_count: number;
  articles: PublicArticleSummary[];
};

const EMPTY_JOURNAL: PublicJournalResponse = {
  published_count: 0,
  articles: [],
};

/**
 * حالة المجلة العامة من الخادم — مصدر الحقيقة لانتقال واجهة الرئيسية.
 * عند published_count = 0 تُعرض واجهة المرحلة المبكرة؛ وإلا واجهة المجلة الغنية.
 */
export async function fetchPublicJournal(): Promise<PublicJournalResponse> {
  try {
    const response = await fetch(`${API_BASE}/api/v1/public/journal`, {
      next: { revalidate: 60 },
    });
    if (!response.ok) {
      return EMPTY_JOURNAL;
    }
    return (await response.json()) as PublicJournalResponse;
  } catch {
    return EMPTY_JOURNAL;
  }
}

export function formatPublicAuthors(authors: PublicArticleAuthor[]): string {
  const names = [...authors]
    .sort((a, b) => a.author_order - b.author_order)
    .map((author) => author.full_name?.trim())
    .filter((name): name is string => Boolean(name));
  return names.length > 0 ? names.join("، ") : "—";
}
