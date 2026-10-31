// Set the flag without shell-specific syntax so this works in cmd and PowerShell.
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const vitest = fileURLToPath(new URL('../node_modules/vitest/vitest.mjs', import.meta.url));
const result = spawnSync(process.execPath, [vitest, 'run', 'src/backend.integration.test.js'], {
  stdio: 'inherit',
  env: { ...process.env, ARLO_INTEGRATION: '1' },
});
if (result.error) {
  console.error('Could not start integration tests:', result.error.message);
}
process.exitCode = result.status ?? 1;
