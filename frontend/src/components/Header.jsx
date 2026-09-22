export default function Header() {
  return (
    <header className="app-header">
      <div className="flex items-center gap-4">
        <img
          src="/maxdenta-logo.jpg"
          alt="MaxDenta Lab"
          className="h-14 w-auto object-contain sm:h-[4.25rem]"
        />
        <div className="hidden h-10 w-px bg-white/20 md:block" />
        <div className="hidden md:block">
          <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-white/55">
            Operations
          </p>
          <p className="text-sm font-medium tracking-[0.04em] text-white">
            Master Data Office
          </p>
        </div>
      </div>
      <div className="hidden text-right sm:block">
        <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-white/55">
          Exclusive for Clear Aligners
        </p>
        <p className="text-xs text-white/75">Production &amp; Distribution Control</p>
      </div>
    </header>
  )
}
