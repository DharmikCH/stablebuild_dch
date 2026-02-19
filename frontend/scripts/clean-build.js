import fs from 'fs';
import path from 'path';

function removeDirectory(dir) {
  if (fs.existsSync(dir)) {
    fs.rmSync(dir, { recursive: true, force: true });
    console.log(`[v0] Removed ${dir}`);
  }
}

// Remove .next build cache
removeDirectory('.next');

// Remove node_modules
removeDirectory('node_modules');

console.log('[v0] Build cache cleaned successfully');
