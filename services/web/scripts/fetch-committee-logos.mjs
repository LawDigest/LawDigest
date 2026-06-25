import { mkdir, writeFile } from 'node:fs/promises';

const BASE_URL = 'https://committee.na.go.kr';
const OUTPUT_DIR = new URL('../public/images/committees/', import.meta.url);

const LOGOS = [
  ['committee', '/commitee/committee/img/m_logo_committee.jpg'],
  ['steering', '/commitee/steering/img/m_logo_steering.jpg'],
  ['legislation', '/commitee/legislation/img/m_logo_legislation.jpg'],
  ['policy', '/commitee/policy/img/m_logo_policy.jpg'],
  ['finance', '/commitee/finance/img/m_logo_finance.jpg'],
  ['edu', '/commitee/edu/img/m_logo_edu.jpg'],
  ['science', '/commitee/science/img/m_logo_science.jpg'],
  ['uft', '/commitee/uft/img/m_logo_uft.jpg'],
  ['defense', '/commitee/defense/img/m_logo_defense.jpg'],
  ['adminhom', '/commitee/adminhom/img/m_logo_adminhom.jpg'],
  ['cst', '/commitee/cst/img/m_logo_cst.jpg'],
  ['agri', '/commitee/agri/img/m_logo_agri.jpg'],
  ['industry', '/commitee/industry/img/m_logo_industry.jpg'],
  ['health', '/commitee/health/img/m_logo_health.jpg'],
  ['environment', '/commitee/environment/img/m_logo_environment.jpg'],
  ['ltc', '/commitee/ltc/img/m_logo_ltc.jpg'],
  ['intelligence', '/commitee/intelligence/img/m_logo_intelligence.jpg'],
  ['women', '/commitee/women/img/m_logo_women.jpg'],
  ['budget', '/commitee/budget/img/m_logo_budget.jpg'],
  ['moral', '/commitee/moral/img/m_logo_moral.jpg'],
  ['spc', '/commitee/spc/img/m_logo_spc.jpg'],
];

async function fetchLogo([key, path]) {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: {
      'user-agent': 'Mozilla/5.0',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch ${path}: ${response.status}`);
  }

  const buffer = Buffer.from(await response.arrayBuffer());
  await writeFile(new URL(`${key}.jpg`, OUTPUT_DIR), buffer);
}

await mkdir(OUTPUT_DIR, { recursive: true });
await Promise.all(LOGOS.map(fetchLogo));

console.log(`Fetched ${LOGOS.length} committee logos from ${BASE_URL}`);
