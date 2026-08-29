"use client";

import { useAuth } from "@clerk/nextjs";
import Image from "next/image";
import { useEffect, useState } from "react";
import {
  fetchIssueImageBlob,
  type IssueImage,
} from "@/lib/api/issues";

export function IssueImageThumbnail({
  issueId,
  image,
  onDelete,
  deleting = false,
}: {
  issueId: string;
  image: IssueImage;
  onDelete?: (imageId: string) => void;
  deleting?: boolean;
}) {
  const { getToken } = useAuth();
  const [src, setSrc] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let url: string | null = null;
    let cancelled = false;

    setSrc(null);
    setError(null);
    fetchIssueImageBlob(getToken, issueId, image.id)
      .then((blob) => {
        if (cancelled) return;
        url = URL.createObjectURL(blob);
        setSrc(url);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "تعذّر تحميل الصورة.");
        }
      });

    return () => {
      cancelled = true;
      if (url) URL.revokeObjectURL(url);
    };
  }, [getToken, image.id, issueId]);

  return (
    <div className="relative overflow-hidden rounded-md border border-[var(--journal-border)] bg-slate-50">
      <div className="relative aspect-[4/3] w-full">
        {src ? (
          <Image
            src={src}
            alt=""
            fill
            unoptimized
            sizes="(max-width: 640px) 50vw, 220px"
            className="object-cover"
          />
        ) : (
          <div className="flex h-full items-center justify-center px-3 text-center text-xs text-slate-500">
            {error ?? "جارٍ تحميل الصورة..."}
          </div>
        )}
      </div>
      {onDelete ? (
        <button
          type="button"
          onClick={() => onDelete(image.id)}
          disabled={deleting}
          className="absolute end-2 top-2 rounded-md bg-white/95 px-2 py-1 text-xs font-semibold text-red-700 shadow-sm transition hover:bg-red-50 disabled:cursor-wait disabled:opacity-70"
        >
          حذف
        </button>
      ) : null}
    </div>
  );
}
