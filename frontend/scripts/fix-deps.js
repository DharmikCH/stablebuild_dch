import fs from 'fs';
import path from 'path';

const targetDir = '/vercel/share/v0-next-shadcn';
const lockPath = path.join(targetDir, 'pnpm-lock.yaml');

console.log('[v0] Fixing dependencies in dev environment...');

// Delete stale lock file
try {
  if (fs.existsSync(lockPath)) {
    fs.unlinkSync(lockPath);
    console.log('[v0] Deleted stale pnpm-lock.yaml from dev environment');
  }
} catch (err) {
  console.log('[v0] Error deleting lock file:', err.message);
}

// Delete .next cache
const nextCachePath = path.join(targetDir, '.next');
try {
  if (fs.existsSync(nextCachePath)) {
    fs.rmSync(nextCachePath, { recursive: true, force: true });
    console.log('[v0] Deleted .next cache');
  }
} catch (err) {
  console.log('[v0] Error deleting .next:', err.message);
}

console.log('[v0] Dev environment cleaned. Dependencies will reinstall on next start.');
