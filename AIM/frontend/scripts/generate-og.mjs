// Generate OG image from SVG
// Usage: node scripts/generate-og.mjs
import { execSync } from "child_process";
import { writeFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));

const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#0284c7;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#0c4a6e;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)"/>
  <rect x="60" y="60" width="1080" height="510" rx="24" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="2"/>

  <!-- Logo -->
  <rect x="80" y="80" width="80" height="80" rx="16" fill="white" opacity="0.15"/>
  <text x="120" y="135" font-family="system-ui,-apple-system,sans-serif" font-size="48" font-weight="800" fill="white" text-anchor="middle">A</text>

  <text x="180" y="135" font-family="system-ui,-apple-system,sans-serif" font-size="36" font-weight="700" fill="white">AIM Agency</text>

  <!-- Main headline -->
  <text x="600" y="320" font-family="system-ui,-apple-system,sans-serif" font-size="56" font-weight="800" fill="white" text-anchor="middle">
    AI-маркетинг
  </text>
  <text x="600" y="385" font-family="system-ui,-apple-system,sans-serif" font-size="56" font-weight="800" fill="white" text-anchor="middle">
    для медицинских клиник
  </text>

  <!-- Subheadline -->
  <text x="600" y="440" font-family="system-ui,-apple-system,sans-serif" font-size="24" font-weight="400" fill="rgba(255,255,255,0.8)" text-anchor="middle">
    Привлекаем пациентов с помощью AI • Гарантия результата
  </text>

  <!-- Stats -->
  <rect x="140" y="480" width="280" height="80" rx="12" fill="rgba(255,255,255,0.1)"/>
  <text x="280" y="515" font-family="system-ui,-apple-system,sans-serif" font-size="28" font-weight="700" fill="white" text-anchor="middle">300%</text>
  <text x="280" y="542" font-family="system-ui,-apple-system,sans-serif" font-size="14" font-weight="400" fill="rgba(255,255,255,0.7)" text-anchor="middle">Рост трафика</text>

  <rect x="460" y="480" width="280" height="80" rx="12" fill="rgba(255,255,255,0.1)"/>
  <text x="600" y="515" font-family="system-ui,-apple-system,sans-serif" font-size="28" font-weight="700" fill="white" text-anchor="middle">450%</text>
  <text x="600" y="542" font-family="system-ui,-apple-system,sans-serif" font-size="14" font-weight="400" fill="rgba(255,255,255,0.7)" text-anchor="middle">ROI</text>

  <rect x="780" y="480" width="280" height="80" rx="12" fill="rgba(255,255,255,0.1)"/>
  <text x="920" y="515" font-family="system-ui,-apple-system,sans-serif" font-size="28" font-weight="700" fill="white" text-anchor="middle">50+</text>
  <text x="920" y="542" font-family="system-ui,-apple-system,sans-serif" font-size="14" font-weight="400" fill="rgba(255,255,255,0.7)" text-anchor="middle">Клиник</text>

  <!-- URL -->
  <text x="600" y="600" font-family="system-ui,-apple-system,sans-serif" font-size="18" font-weight="500" fill="rgba(255,255,255,0.5)" text-anchor="middle">iamaim.ru</text>
</svg>`;

const svgPath = join(__dirname, "..", "public", "og-image.svg");
const pngPath = join(__dirname, "..", "public", "og-image.png");

writeFileSync(svgPath, svg);
console.log("SVG template written to", svgPath);

try {
  execSync(`npx @aspect-build/rsc convert ${svgPath} ${pngPath} 2>/dev/null || true`);
} catch {}

console.log("To generate PNG, install sharp and run: npx svg2png ${svgPath} -o ${pngPath}");
console.log("Or use: npm run generate-og");
