import { cpSync, existsSync, rmSync } from 'node:fs'
import { spawnSync } from 'node:child_process'
import path from 'node:path'

const repositoryRoot = path.resolve(import.meta.dirname, '..')
const npmCli = process.env.npm_execpath
const command = npmCli
  ? [process.execPath, npmCli, '--prefix', 'frontend', 'run', 'build']
  : [process.platform === 'win32' ? 'npm.cmd' : 'npm', '--prefix', 'frontend', 'run', 'build']

const result = spawnSync(command[0], command.slice(1), {
  cwd: repositoryRoot,
  env: process.env,
  stdio: 'inherit',
})

if (result.error) throw result.error
if (result.status !== 0) process.exit(result.status ?? 1)

const frontendOutput = path.join(repositoryRoot, 'frontend', 'dist')
const sitesOutput = path.join(repositoryRoot, 'dist')
if (!existsSync(path.join(frontendOutput, 'server', 'index.js'))) {
  throw new Error('Frontend build did not produce the Sites Worker entrypoint')
}

rmSync(sitesOutput, { force: true, recursive: true })
cpSync(frontendOutput, sitesOutput, { recursive: true })
