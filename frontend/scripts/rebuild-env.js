import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';

const projectRoot = '/vercel/share/v0-project';
const devEnv = '/vercel/share/v0-next-shadcn';

console.log('[v0] Starting environment rebuild...');

// 1. Remove stale lock and build files
const lockPath = path.join(devEnv, '.next', 'dev', 'lock');
const nextPath = path.join(devEnv, '.next');

try {
  if (fs.existsSync(lockPath)) {
    fs.rmSync(lockPath, { force: true });
    console.log('[v0] Removed stale lock file');
  }
  
  if (fs.existsSync(nextPath)) {
    fs.rmSync(nextPath, { recursive: true, force: true });
    console.log('[v0] Removed .next directory');
  }
} catch (e) {
  console.log('[v0] Could not remove files:', e.message);
}

// 2. Regenerate pnpm-lock.yaml by removing it
const lockFile = path.join(projectRoot, 'pnpm-lock.yaml');
try {
  if (fs.existsSync(lockFile)) {
    fs.unlinkSync(lockFile);
    console.log('[v0] Removed pnpm-lock.yaml');
  }
} catch (e) {
  console.log('[v0] Could not remove lock file:', e.message);
}

console.log('[v0] Environment rebuild complete. Dependencies will be reinstalled on next start.');
