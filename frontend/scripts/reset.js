import fs from 'fs';
import path from 'path';

const projectDir = '/vercel/share/v0-project';
const devDir = '/vercel/share/v0-next-shadcn';

console.log('[v0] Starting reset of dev environment...');

try {
  // Remove stale lock files
  const lockFiles = [
    `${projectDir}/pnpm-lock.yaml`,
    `${projectDir}/package-lock.json`,
    `${devDir}/pnpm-lock.yaml`,
    `${devDir}/package-lock.json`,
  ];
  
  for (const file of lockFiles) {
    if (fs.existsSync(file)) {
      fs.rmSync(file);
      console.log(`[v0] Deleted ${file}`);
    }
  }
  
  // Remove .next build cache from dev dir
  if (fs.existsSync(`${devDir}/.next`)) {
    fs.rmSync(`${devDir}/.next`, { recursive: true, force: true });
    console.log(`[v0] Deleted ${devDir}/.next`);
  }
  
  // Remove .next build cache from project dir
  if (fs.existsSync(`${projectDir}/.next`)) {
    fs.rmSync(`${projectDir}/.next`, { recursive: true, force: true });
    console.log(`[v0] Deleted ${projectDir}/.next`);
  }
  
  // Remove node_modules from dev dir
  if (fs.existsSync(`${devDir}/node_modules`)) {
    fs.rmSync(`${devDir}/node_modules`, { recursive: true, force: true });
    console.log(`[v0] Deleted ${devDir}/node_modules`);
  }
  
  console.log('[v0] Reset complete - dependencies will be reinstalled automatically');
} catch (error) {
  console.error('[v0] Reset error:', error.message);
  process.exit(1);
}
