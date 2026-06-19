/**
 * ExamLensLogo — Brand icon for ExamLens
 *
 * A bold, minimal lens circle with ascending score bars inside.
 * Designed to be instantly readable at 20px in the dark sidebar,
 * and scale beautifully up to 120px on the landing page.
 *
 * Props:
 *   size  — width & height in px (default 24)
 */

export default function ExamLensLogo({ size = 24 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="ExamLens"
    >
      {/* Lens circle */}
      <circle
        cx="21" cy="21" r="17"
        stroke="#0D9488"
        strokeWidth="3.5"
        fill="none"
      />

      {/* Score bars inside the lens — the "analysis" */}
      <rect x="12" y="24" width="5" height="8"  rx="1.5" fill="#14B8A6" />
      <rect x="19" y="19" width="5" height="13" rx="1.5" fill="#0D9488" />
      <rect x="26" y="14" width="5" height="18" rx="1.5" fill="#0D9488" />

      {/* Lens handle */}
      <line
        x1="33" y1="33"
        x2="44" y2="44"
        stroke="#0D9488"
        strokeWidth="4"
        strokeLinecap="round"
      />
    </svg>
  )
}
