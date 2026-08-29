import Image from "next/image";

export function HeroBrandMark() {
  return (
    <div className="mx-auto flex justify-center">
      <Image
        src="/official-logo.png"
        alt="شعار مجلة البيان"
        width={160}
        height={160}
        priority
        className="h-24 w-24 object-contain drop-shadow-[0_14px_26px_rgba(18,63,51,0.18)] sm:h-32 sm:w-32 lg:h-36 lg:w-36"
      />
    </div>
  );
}
