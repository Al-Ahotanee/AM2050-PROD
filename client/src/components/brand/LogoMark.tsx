/* AM2050 — Field Ledger Modernism: a simple, durable symbol that anchors the app rail. */
type LogoMarkProps = { className?: string; size?: number };

export function LogoMark({ className = "", size = 40 }: LogoMarkProps) {
  return (
    <img
      src="/manus-storage/am2050-logo-mark_b4ca4fe7.png"
      alt="AM2050 mission mark"
      width={size}
      height={size}
      className={`object-contain ${className}`}
    />
  );
}
