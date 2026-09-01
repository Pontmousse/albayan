import Image from "next/image";
import type { UserGender } from "@/lib/api";

type GenderIconSelectorProps = {
  value: UserGender | null;
  onChange: (gender: UserGender) => void;
  disabled?: boolean;
  name?: string;
};

const OPTIONS: Array<{
  value: UserGender;
  src: string;
  accessibleLabel: string;
}> = [
  { value: "male", src: "/male.png", accessibleLabel: "مذكر" },
  { value: "female", src: "/female.png", accessibleLabel: "مؤنث" },
];

export function GenderIconSelector({
  value,
  onChange,
  disabled = false,
  name = "gender",
}: GenderIconSelectorProps) {
  return (
    <fieldset disabled={disabled} className="min-w-0">
      <legend className="sr-only">صيغة المخاطبة</legend>
      <div className="flex items-center gap-2" role="radiogroup">
        {OPTIONS.map((option) => {
          const selected = value === option.value;
          return (
            <label
              key={option.value}
              className={`flex size-16 cursor-pointer items-center justify-center overflow-hidden rounded-xl border bg-white transition focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-[var(--journal-accent)] ${
                selected
                  ? "border-[var(--journal-accent)] bg-[var(--journal-accent-soft)] shadow-sm"
                  : "border-[var(--journal-border)] hover:border-[var(--journal-accent)]"
              } ${disabled ? "cursor-default opacity-70" : ""}`}
            >
              <input
                type="radio"
                name={name}
                value={option.value}
                checked={selected}
                onChange={() => onChange(option.value)}
                className="sr-only"
                aria-label={option.accessibleLabel}
              />
              <Image
                src={option.src}
                alt=""
                width={48}
                height={48}
                className="size-12 object-contain"
              />
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}
